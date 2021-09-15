"""Contract test cases for ping."""
import asyncio
import logging
import os
from typing import Any, Optional

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
async def raceplan_id(http_service: Any, token: MockFixture) -> Optional[str]:
    """Create an raceplan object for testing."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = {
        "name": "Oslo Skagen sprint",
        "date": "2021-08-31",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }
    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
    await session.close()
    if status == 201:
        # return the raceplan_id, which is the last item of the path
        return response.headers[hdrs.LOCATION].split("/")[-1]
    else:
        logging.error(f"Got unsuccesful status when creating raceplan: {status}.")
        return None


@pytest.mark.contract
@pytest.mark.asyncio
async def test_generate_raceplan_for_event(
    http_service: Any, token: MockFixture, raceplan_id: str
) -> None:
    """Should return 201 created and a location header with url to raceplan."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
        hdrs.CONTENT_TYPE: "application/json",
    }

    async with ClientSession() as session:
        # Finally ageclasses are generated:
        url = f"{http_service}/raceplans/{raceplan_id}/generate-plan-for-event"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/raceplans/{raceplan_id}" in response.headers[hdrs.LOCATION]

        # We check that ageclasses are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url, headers=headers) as response:
            ageclasses = await response.json()
            assert response.status == 200
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(ageclasses) is list
            assert len(ageclasses) > 0
