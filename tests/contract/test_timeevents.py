"""Contract test cases for raceclasses."""
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
    """Delete all timeevents before we start."""
    url = f"{http_service}/timeevents"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        timeevents = await response.json()
        for timeevent in timeevents:
            timeevent_id = timeevent["id"]
            async with session.delete(
                f"{url}/{timeevent_id}", headers=headers
            ) as response:
                pass
    await session.close()
    yield


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
async def new_timeevent() -> dict:
    """Create a timeevent object."""
    return {
        "bib": 14,
        "event_id": "event_1",
        "race_id": "race_1",
        "point": "Finish",
        "rank": 0,
        "registration_time": datetime.fromisoformat("2021-08-31 12:01:02").isoformat(),
        "next_race_id": "semi_1",
        "status": "OK",
        "changelog": [
            {
                "timestamp": "2021-08-31 12:00:02",
                "userId": "raceplan-admin",
                "comment": "First status change to",
            },
            {
                "timestamp": "2021-08-31 12:01:02",
                "userId": "raceplan-admin",
                "comment": "Second status change to",
            },
        ],
    }


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_timeevent(
    http_service: Any, token: MockFixture, clear_db: None, new_timeevent: dict
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/timeevents"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = dumps(new_timeevent, indent=4, sort_keys=True, default=str)

    session = ClientSession()
    async with session.post(url, headers=headers, data=request_body) as response:
        status = response.status
    await session.close()
    assert status == 201
    assert "/timeevents/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_timeevents(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of timeevents as json."""
    url = f"{http_service}/timeevents"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        timeevents = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(timeevents) is list
    assert len(timeevents) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_timeevent_by_event_id(
    http_service: Any, token: MockFixture, new_timeevent: dict
) -> None:
    """Should return OK and a list with one timeevent as json."""
    event_id = new_timeevent["event_id"]
    url = f"{http_service}/timeevents?event-id={event_id}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        timeevents = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(timeevents) is list
    assert len(timeevents) == 1
    assert timeevents[0]["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_timeevent(
    http_service: Any, token: MockFixture, new_timeevent: dict
) -> None:
    """Should return OK and an timeevent as json."""
    url = f"{http_service}/timeevents"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            timeevents = await response.json()
        id = timeevents[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url, headers=headers) as response:
            timeevent = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(timeevent) is dict
    assert timeevent["id"]
    assert timeevent["event_id"] == new_timeevent["event_id"]
    assert timeevent["races"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_timeevent(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/timeevents"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            timeevents = await response.json()
        id = timeevents[0]["id"]
        url = f"{url}/{id}"
        update_timeevent = deepcopy(timeevents[0])
        update_timeevent["event_id"] = "new_event_id"
        request_body = dumps(update_timeevent, indent=4, sort_keys=True, default=str)
        async with session.put(url, headers=headers, data=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_timeevent(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/timeevents"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            timeevents = await response.json()
        id = timeevents[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_timeevent_by_event_id_when_event_does_not_exist(
    http_service: Any, token: MockFixture, new_timeevent: dict
) -> None:
    """Should return OK and an empty list."""
    event_id = "does_not_exist"
    url = f"{http_service}/timeevents?event-id={event_id}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        timeevents = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(timeevents) is list
    assert len(timeevents) == 0
