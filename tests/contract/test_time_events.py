"""Contract test cases for raceclasses."""
import asyncio
from copy import deepcopy
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
    await delete_time_events(http_service, token)
    logging.info(" --- Testing starts. ---")
    yield
    logging.info(" --- Testing finished. ---")
    logging.info(" --- Cleaning db after testing. ---")
    await delete_time_events(http_service, token)
    logging.info(" --- Cleaning db done. ---")


async def delete_time_events(http_service: Any, token: MockFixture) -> None:
    """Delete all time_events before we start."""
    url = f"{http_service}/time-events"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            time_events = await response.json()
            for time_event in time_events:
                time_event_id = time_event["id"]
                async with session.delete(
                    f"{url}/{time_event_id}", headers=headers
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
async def new_time_event() -> dict:
    """Create a time_event object."""
    return {
        "bib": 14,
        "event_id": "event_1",
        "race_id": "race_1",
        "point": "Finish",
        "rank": "0",
        "registration_time": "12:01:02",
        "next_race_id": "semi_1",
        "status": "OK",
        "changelog": "",
    }


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_time_event(
    http_service: Any, token: MockFixture, clear_db: None, new_time_event: dict
) -> None:
    """Should return Created, location header and no body."""
    url = f"{http_service}/time-events"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = dumps(new_time_event, indent=4, sort_keys=True, default=str)

    session = ClientSession()
    async with session.post(url, headers=headers, data=request_body) as response:
        status = response.status
    await session.close()
    assert status == 201
    assert "/time-events/" in response.headers[hdrs.LOCATION]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_time_events(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of time_events as json."""
    url = f"{http_service}/time-events"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        time_events = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(time_events) is list
    assert len(time_events) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_time_events_by_event_id(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and a list with one time_event as json."""
    event_id = new_time_event["event_id"]
    url = f"{http_service}/time-events?eventId={event_id}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        time_events = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(time_events) is list
    assert len(time_events) == 1
    assert time_events[0]["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_time_event(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and an time_event as json."""
    url = f"{http_service}/time-events"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            time_events = await response.json()
        id = time_events[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url, headers=headers) as response:
            time_event = await response.json()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(time_event) is dict
    assert time_event["id"]
    assert time_event["event_id"] == new_time_event["event_id"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_update_time_event(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/time-events"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            time_events = await response.json()
        id = time_events[0]["id"]
        url = f"{url}/{id}"
        update_time_event = deepcopy(time_events[0])
        update_time_event["event_id"] = "new_event_id"
        request_body = dumps(update_time_event, indent=4, sort_keys=True, default=str)
        async with session.put(url, headers=headers, data=request_body) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_time_event(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/time-events"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            time_events = await response.json()
        id = time_events[0]["id"]
        url = f"{url}/{id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_time_event_by_event_id_when_event_does_not_exist(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and an empty list."""
    event_id = "does_not_exist"
    url = f"{http_service}/time-events?eventId={event_id}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        time_events = await response.json()
    await session.close()

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(time_events) is list
    assert len(time_events) == 0
