"""Contract test cases for raceclasses."""
import asyncio
from copy import deepcopy
from datetime import time
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
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        raceplans = await response.json()
        for raceplan in raceplans:
            raceplan_id = raceplan["id"]
            async with session.delete(
                f"{url}/{raceplan_id}", headers=headers
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
async def new_raceplan() -> dict:
    """Create a raceplan object."""
    return {
        "event_id": "event_1",
        "races": [
            {
                "name": "G16K01",
                "raceclass": "G16",
                "order": 1,
                "start_time": time(12, 00, 00).isoformat(),
            },
            {
                "name": "G16K02",
                "raceclass": "G16",
                "order": 2,
                "start_time": time(12, 15, 00).isoformat(),
            },
            {
                "name": "G16K03",
                "raceclass": "G16",
                "order": 3,
                "start_time": time(12, 30, 00).isoformat(),
            },
            {
                "name": "G16K04",
                "raceclass": "G16",
                "order": 4,
                "start_time": time(12, 45, 00).isoformat(),
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
    request_body = new_raceplan
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()

    assert status == 201
    assert "/raceplans/" in response.headers[hdrs.LOCATION]


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
        request_body = deepcopy(raceplans[0])
        request_body["event_id"] = "new_event_id"
        async with session.put(url, headers=headers, json=request_body) as response:
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
