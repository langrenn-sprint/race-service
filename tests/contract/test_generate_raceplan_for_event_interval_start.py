"""Contract test cases for ping."""
import asyncio
from json import load
import logging
import os
from typing import Any, AsyncGenerator, Optional

from aiohttp import ClientSession, hdrs
import pytest
from pytest_mock import MockFixture

EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT")
USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture(scope="module")
def event_loop(request: Any) -> Any:
    """Redefine the event_loop fixture to have the same scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def clear_db(
    http_service: Any, token: MockFixture, event_id: str
) -> AsyncGenerator:
    """Clear db before and after tests."""
    logging.info(" --- Cleaning db at startup. ---")
    await delete_raceplans(http_service, token)
    await delete_contestants(token, event_id)
    await delete_raceclasses(token, event_id)
    logging.info(" --- Testing starts. ---")
    yield
    logging.info(" --- Testing finished. ---")
    logging.info(" --- Cleaning db after testing. ---")
    await delete_raceplans(http_service, token)
    await delete_contestants(token, event_id)
    await delete_raceclasses(token, event_id)
    await delete_event(token, event_id)
    logging.info(" --- Cleaning db done. ---")


async def delete_event(token: MockFixture, event_id: str) -> None:
    """Delete all events."""
    url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.delete(f"{url}", headers=headers) as response:
        assert response.status == 204
    await session.close()
    logging.info("Clear_db: Deleted all events.")


async def delete_contestants(token: MockFixture, event_id: str) -> None:
    """Delete all contestants."""
    url = (
        f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.delete(url, headers=headers) as response:
        assert response.status == 204
    await session.close()
    logging.info("Clear_db: Deleted all contestants.")


async def delete_raceclasses(token: MockFixture, event_id: str) -> None:
    """Delete all raceclasses."""
    url = (
        f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/raceclasses"
    )
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    session = ClientSession()
    async with session.get(url, headers=headers) as response:
        raceclasses = await response.json()
        for raceclass in raceclasses:
            raceclass_id = raceclass["id"]
            async with session.delete(
                f"{url}/{raceclass_id}", headers=headers
            ) as response:
                assert response.status == 204
    await session.close()
    logging.info("Clear_db: Deleted all raceclasses.")


async def delete_raceplans(http_service: Any, token: MockFixture) -> None:
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
    logging.info("Clear_db: Deleted all raceplans.")


# Create an event to test on:
@pytest.fixture(scope="module")
async def event_id(
    http_service: Any, token: MockFixture, competition_format_interval_start: Any
) -> Optional[str]:
    """Create an event object for testing."""
    url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
    with open("tests/files/event_interval_start.json", "r") as file:
        event = load(file)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = event

    session = ClientSession()
    async with session.post(url, headers=headers, json=request_body) as response:
        status = response.status
        if status != 201:
            body = await response.json()
    await session.close()
    if status == 201:
        # return the event_id, which is the last item of the path
        return response.headers[hdrs.LOCATION].split("/")[-1]
    else:
        logging.error(
            f"Got unsuccesful status when creating event: {status}, reason {body}."
        )
    return None


@pytest.fixture(scope="module")
async def competition_format_interval_start(
    http_service: Any, token: MockFixture
) -> Any:
    """An competition_format object for testing."""
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    with open("tests/files/competition_format.json", "r") as file:
        competition_format = load(file)
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats"
        request_body = competition_format
        session = ClientSession()
        async with session.post(url, headers=headers, json=request_body) as response:
            status = response.status
        await session.close()
        assert status == 201


@pytest.fixture
async def expected_raceplan() -> dict:
    """Create a mock raceplan object."""
    with open("tests/files/expected_raceplan.json", "r") as file:
        raceplan = load(file)

    return raceplan


# Finally we test the test_generate_raceplan_for_event function:
@pytest.mark.contract
@pytest.mark.asyncio
async def test_generate_raceplan_for__interval_start_event(
    http_service: Any,
    token: MockFixture,
    clear_db: None,
    event_id: str,
    expected_raceplan: dict,
) -> None:
    """Should return 201 created and a location header with url to raceplan."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    event_id = event_id
    async with ClientSession() as session:
        # First we need to assert that we have an event:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}"
        logging.debug(f"Verifying event with id {event_id} at url {url}.")
        async with session.get(url, headers=headers) as response:
            assert response.status == 200

        # Add list of contestants to event:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        files = {"file": open("tests/files/allcontestants_eventid_364892.csv", "rb")}
        logging.debug(f"Adding contestants from file at url {url}.")
        async with session.post(url, headers=headers, data=files) as response:
            status = response.status
            body = await response.json()
            if response.status != 200:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
            assert status == 200

        # Generate raceclasses based on contestants:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/generate-raceclasses"
        )
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        # Set order on all raceclasses:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses"
        )
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceclasses = await response.json()
            # TODO: do some kind of sorting so that we can compare results
            order = 0
            for raceclass in raceclasses:
                id = raceclass["id"]
                order = order + 1
                raceclass["order"] = order
                async with session.put(
                    f"{url}/{id}", headers=headers, json=raceclass
                ) as response:
                    assert response.status == 204

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 201:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
            assert response.status == 201
            assert "/raceplans/" in response.headers[hdrs.LOCATION]

        # We check that raceplan are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            # And we compare the response to the expected raceplan:
            assert (
                raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
            )
            assert len(raceplan["races"]) == len(expected_raceplan["races"])

            i = 0
            for race in raceplan["races"]:
                expected_race = expected_raceplan["races"][i]
                assert race["order"] == i + 1
                assert (
                    race["order"] == expected_race["order"]
                ), f'"order" in index {i}:{race}\n ne:\n{expected_race}'
                assert (
                    race["raceclass"] == expected_raceplan["races"][i]["raceclass"]
                ), f'"raceclass" in index {i}:{race}\n ne:\n{expected_race}'
                assert (
                    race["start_time"] == expected_raceplan["races"][i]["start_time"]
                ), f'"start_time" in index {i}:{race}\n ne:\n{expected_race}'
                assert (
                    race["no_of_contestants"]
                    == expected_raceplan["races"][i]["no_of_contestants"]
                ), f'"no_of_contestants" in index {i}:{race}\n ne:\n{expected_race}'
                i += 1
