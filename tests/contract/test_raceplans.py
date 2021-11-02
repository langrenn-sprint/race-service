"""Contract test cases for raceplans."""
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
    """Delete all raceplans before we start."""
    """Clear db before and after tests."""
    logging.info(" --- Cleaning db at startup. ---")
    await delete_raceplans(http_service, token)
    logging.info(" --- Testing starts. ---")
    yield
    logging.info(" --- Testing finished. ---")
    logging.info(" --- Cleaning db after testing. ---")
    await delete_raceplans(http_service, token)
    logging.info(" --- Cleaning db done. ---")


async def delete_raceplans(http_service: Any, token: MockFixture) -> None:
    """Delete all raceplans before we start."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            raceplans = await response.json()
            for raceplan in raceplans:
                raceplan_id = raceplan["id"]
                async with session.delete(
                    f"{url}/{raceplan_id}", headers=headers
                ) as response:
                    pass
    logging.info("Clear_db: Deleted all raceplans.")


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
async def new_raceplan() -> dict:
    """Create a raceplan object."""
    return {
        "event_id": "event_1",
        "no_of_contestants": 32,
        "races": [
            {
                "name": "G16K01",
                "raceclass": "G16",
                "order": 1,
                "start_time": datetime.fromisoformat("2021-08-31 12:00:00").isoformat(),
                "no_of_contestants": 8,
                "datatype": "interval_start",
            },
            {
                "name": "G16K02",
                "raceclass": "G16",
                "order": 2,
                "start_time": datetime.fromisoformat("2021-08-31 12:15:00").isoformat(),
                "no_of_contestants": 8,
                "datatype": "interval_start",
            },
            {
                "name": "G16K03",
                "raceclass": "G16",
                "order": 3,
                "start_time": datetime.fromisoformat("2021-08-31 12:30:00").isoformat(),
                "no_of_contestants": 8,
                "datatype": "interval_start",
            },
            {
                "name": "G16K04",
                "raceclass": "G16",
                "order": 4,
                "start_time": datetime.fromisoformat("2021-08-31 12:45:00").isoformat(),
                "no_of_contestants": 8,
                "datatype": "interval_start",
            },
        ],
    }


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_raceplan(
    http_service: Any, token: MockFixture, clear_db: None, new_raceplan: dict
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = dumps(new_raceplan, indent=4, sort_keys=True, default=str)

    session = ClientSession()
    async with session.post(url, headers=headers, data=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert "/raceplans/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_raceplan_when_event_already_has_one(
    http_service: Any, token: MockFixture, clear_db: None, new_raceplan: dict
) -> None:
    """Should return 400 Bad request and error message in body."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = dumps(new_raceplan, indent=4, sort_keys=True, default=str)

    session = ClientSession()
    async with session.post(url, headers=headers, data=request_body) as response:
        status = response.status
        body = await response.json()
    await session.close()

    assert status == 400
    assert body
    assert f'"{new_raceplan["event_id"]}" already has a raceplan' in body["detail"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_raceplans(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of raceplans as json."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        raceplans = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceplans) is list
    assert len(raceplans) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_raceplan_by_event_id(
    http_service: Any, token: MockFixture, new_raceplan: dict
) -> None:
    """Should return OK and a list with one raceplan as json."""
    event_id = new_raceplan["event_id"]
    url = f"{http_service}/raceplans?eventId={event_id}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        raceplans = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceplans) is list
    assert len(raceplans) == 1
    assert raceplans[0]["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_raceplan(
    http_service: Any, token: MockFixture, new_raceplan: dict
) -> None:
    """Should return OK and an raceplan as json."""
    url = f"{http_service}/raceplans"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            raceplans = await response.json()
        id = raceplans[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url, headers=headers) as response:
            raceplan = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceplan) is dict
    assert raceplan["id"]
    assert raceplan["event_id"] == new_raceplan["event_id"]
    assert raceplan["races"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_raceplan(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            raceplans = await response.json()
        id = raceplans[0]["id"]
        url = f"{url}/{id}"
        update_raceplan = deepcopy(raceplans[0])
        update_raceplan["event_id"] = "new_event_id"
        request_body = dumps(update_raceplan, indent=4, sort_keys=True, default=str)
        async with session.put(url, headers=headers, data=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_raceplan(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            raceplans = await response.json()
        id = raceplans[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_raceplan_by_event_id_when_event_does_not_exist(
    http_service: Any, token: MockFixture, new_raceplan: dict
) -> None:
    """Should return OK and an empty list."""
    event_id = "does_not_exist"
    url = f"{http_service}/raceplans?eventId={event_id}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        raceplans = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceplans) is list
    assert len(raceplans) == 0
