"""Contract test cases for ping."""
import asyncio
import logging
import os
from typing import Any, AsyncGenerator

from aiohttp import ClientSession, hdrs
import pytest
from pytest_mock import MockFixture

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture(scope="session")
def event_loop(request: Any) -> Any:
    """Redefine the event_loop fixture to have the same scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
async def request_body() -> dict:
    """Create an raceplan object for testing."""
    return {
        "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "competition_format": "Individual sprint competition",
        "raceclasses": [{"name": "G16", "order": "1"}, {"name": "J16", "order": "2"}],
        "contestants": [
            {"bib": 1, "raceclass": "G16"},
            {"bib": 2, "raceclass": "G16"},
            {"bib": 3, "raceclass": "J16"},
            {"bib": 4, "raceclass": "J16"},
        ],
    }


@pytest.fixture
@pytest.mark.asyncio
async def clear_db(http_service: Any, token: MockFixture) -> AsyncGenerator:
    """Delete all raceplans."""
    yield
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


@pytest.mark.contract
@pytest.mark.asyncio
async def test_generate_raceplan_for_event(
    http_service: Any, token: MockFixture, clear_db: None, request_body: dict
) -> None:
    """Should return 201 created and a location header with url to raceplan."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
        hdrs.CONTENT_TYPE: "application/json",
    }

    async with ClientSession() as session:
        # Raceplan is generated:
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            assert response.status == 201
            assert "/raceplans/" in response.headers[hdrs.LOCATION]

        # We check that raceplan are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url, headers=headers) as response:
            raceplan = await response.json()
            assert response.status == 200
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]
