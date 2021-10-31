"""Contract test cases for startlists."""
import asyncio
from copy import deepcopy
from datetime import datetime
from json import dumps
import logging
import os
from typing import Any, AsyncGenerator

from aiohttp import ClientSession, hdrs
import pytest
from pytest_mock import MockFixture

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture(scope="module")
def event_loop(request: Any) -> Any:
    """Redefine the event_loop fixture to have the same scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def clear_db(http_service: Any, token: MockFixture) -> AsyncGenerator:
    """Delete all startlists before we start."""
    """Clear db before and after tests."""
    logging.info(" --- Cleaning db at startup. ---")
    await delete_startlists(http_service, token)
    logging.info(" --- Testing starts. ---")
    yield
    logging.info(" --- Testing finished. ---")
    logging.info(" --- Cleaning db after testing. ---")
    await delete_startlists(http_service, token)
    logging.info(" --- Cleaning db done. ---")


async def delete_startlists(http_service: Any, token: MockFixture) -> None:
    """Delete all startlists before we start."""
    url = f"{http_service}/startlists"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            startlists = await response.json()
            for startlist in startlists:
                startlist_id = startlist["id"]
                async with session.delete(
                    f"{url}/{startlist_id}", headers=headers
                ) as response:
                    assert response.status == 204
                    pass
    logging.info("Clear_db: Deleted all startlists.")


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def token(http_service: Any) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {hdrs.CONTENT_TYPE: "application/json"}
    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        body = await response.json()
    await session.close()
    if response.status != 200:
        logging.error(f"Got unexpected status {response.status} from {http_service}.")
    return body["token"]


@pytest.fixture
async def new_startlist() -> dict:
    """Create a startlist object."""
    return {
        "event_id": "event_1",
        "no_of_contestants": 4,
        "start_entries": [
            {
                "race_id": "race_1",
                "bib": 1,
                "starting_position": 1,
                "scheduled_start_time": datetime.fromisoformat(
                    "2021-08-31 12:00:00"
                ).isoformat(),
            },
            {
                "race_id": "race_1",
                "bib": 2,
                "starting_position": 2,
                "scheduled_start_time": datetime.fromisoformat(
                    "2021-08-31 12:00:30"
                ).isoformat(),
            },
            {
                "race_id": "race_1",
                "bib": 3,
                "starting_position": 3,
                "scheduled_start_time": datetime.fromisoformat(
                    "2021-08-31 12:01:00"
                ).isoformat(),
            },
            {
                "race_id": "race_1",
                "bib": 4,
                "starting_position": 4,
                "scheduled_start_time": datetime.fromisoformat(
                    "2021-08-31 12:01:30"
                ).isoformat(),
            },
        ],
    }


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_startlist(
    http_service: Any, token: MockFixture, clear_db: None, new_startlist: dict
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/startlists"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = dumps(new_startlist, indent=4, sort_keys=True, default=str)

    session = ClientSession()
    async with session.post(url, headers=headers, data=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert "/startlists/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_startlist_when_event_already_has_one(
    http_service: Any, token: MockFixture, clear_db: None, new_startlist: dict
) -> None:
    """Should return 400 Bad request and error message in body."""
    url = f"{http_service}/startlists"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = dumps(new_startlist, indent=4, sort_keys=True, default=str)

    session = ClientSession()
    async with session.post(url, headers=headers, data=request_body) as response:
        status = response.status
        body = await response.json()
    await session.close()

    assert status == 400
    assert body
    assert f'"{new_startlist["event_id"]}" already has a startlist' in body["detail"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_startlists(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of startlists as json."""
    url = f"{http_service}/startlists"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        startlists = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(startlists) is list
    assert len(startlists) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_startlist_by_event_id(
    http_service: Any, token: MockFixture, new_startlist: dict
) -> None:
    """Should return OK and a list with one startlist as json."""
    event_id = new_startlist["event_id"]
    url = f"{http_service}/startlists?eventId={event_id}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        startlists = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(startlists) is list
    assert len(startlists) == 1
    assert startlists[0]["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_startlist(
    http_service: Any, token: MockFixture, new_startlist: dict
) -> None:
    """Should return OK and an startlist as json."""
    url = f"{http_service}/startlists"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            startlists = await response.json()
        id = startlists[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url, headers=headers) as response:
            body = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(body) is dict
    assert body["id"]
    assert body["event_id"] == new_startlist["event_id"]
    assert body["start_entries"]
    assert len(body["start_entries"]) == len(new_startlist["start_entries"])
    i = 0
    for start_entry in body["start_entries"]:
        assert start_entry["race_id"] == new_startlist["start_entries"][i]["race_id"]
        assert start_entry["bib"] == new_startlist["start_entries"][i]["bib"]
        assert (
            start_entry["starting_position"]
            == new_startlist["start_entries"][i]["starting_position"]
        )
        assert (
            start_entry["scheduled_start_time"]
            == new_startlist["start_entries"][i]["scheduled_start_time"]
        )
        i += 1


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_startlist(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/startlists"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            startlists = await response.json()
        id = startlists[0]["id"]
        url = f"{url}/{id}"
        update_startlist = deepcopy(startlists[0])
        update_startlist["event_id"] = "new_event_id"
        request_body = dumps(update_startlist, indent=4, sort_keys=True, default=str)
        async with session.put(url, headers=headers, data=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_startlist(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/startlists"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            startlists = await response.json()
        id = startlists[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_startlists_by_event_id_when_event_does_not_exist(
    http_service: Any, token: MockFixture, new_startlist: dict
) -> None:
    """Should return OK and an empty list."""
    event_id = "does_not_exist"
    url = f"{http_service}/startlists?eventId={event_id}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        startlists = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(startlists) is list
    assert len(startlists) == 0
