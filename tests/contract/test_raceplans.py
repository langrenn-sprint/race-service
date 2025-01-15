"""Contract test cases for raceplans."""

import json
import logging
import os
from collections.abc import AsyncGenerator
from copy import deepcopy
from http import HTTPStatus
from typing import Any

import motor.motor_asyncio
import pytest
from aiohttp import ClientSession, hdrs
from dotenv import load_dotenv
from pytest_mock import MockFixture

from race_service.utils import db_utils

load_dotenv()

EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT")
COMPETITION_FORMAT_HOST_SERVER = os.getenv("COMPETITION_FORMAT_HOST_SERVER")
COMPETITION_FORMAT_HOST_PORT = os.getenv("COMPETITION_FORMAT_HOST_PORT")
USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "27017"))
DB_NAME = os.getenv("DB_NAME", "races_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


@pytest.fixture(scope="module", autouse=True)
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
    if response.status != HTTPStatus.OK:
        logging.error(f"Got unexpected status {response.status} from {http_service}.")
    return body["token"]


@pytest.fixture(scope="module", autouse=True)
async def clear_db() -> AsyncGenerator:
    """Clear db before and after tests."""
    logging.info(" --- Cleaning db at startup. ---")
    mongo = motor.motor_asyncio.AsyncIOMotorClient(
        host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASSWORD
    )
    try:
        await db_utils.drop_db_and_recreate_indexes(mongo, DB_NAME)
    except Exception as error:
        logging.exception(f"Failed to drop database {DB_NAME}.")
        raise error from error
    logging.info(" --- Testing starts. ---")
    yield
    logging.info(" --- Testing finished. ---")
    logging.info(" --- Cleaning db after testing. ---")
    try:
        await db_utils.drop_db(mongo, DB_NAME)
    except Exception as error:
        logging.exception(f"Failed to drop database {DB_NAME}.")
        raise error from error
    logging.info(" --- Cleaning db done. ---")


# We create a context in which to test the RUD-functins
@pytest.fixture(scope="module", autouse=True)
async def context(
    http_service: Any,
    token: MockFixture,
    clear_db: Any,
) -> dict:
    """Create context and return event_id."""
    event_id = ""
    async with ClientSession() as session:
        # First we need create the competition-format:
        with open("tests/files/competition_format_individual_sprint.json") as file:
            competition_format = json.load(file)
            headers = {
                hdrs.CONTENT_TYPE: "application/json",
                hdrs.AUTHORIZATION: f"Bearer {token}",
            }
            url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"
            request_body = competition_format
            async with session.post(
                url, headers=headers, json=request_body
            ) as response:
                if response.status != HTTPStatus.CREATED:
                    body = await response.json()
                    logging.error(f"When creating competition-format, got error {body}")
                assert response.status == HTTPStatus.CREATED

        # Next we create the event:
        with open("tests/files/event_individual_sprint.json") as file:
            event = json.load(file)

            headers = {
                hdrs.CONTENT_TYPE: "application/json",
                hdrs.AUTHORIZATION: f"Bearer {token}",
            }
            url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
            request_body = event
            async with session.post(
                url, headers=headers, json=request_body
            ) as response:
                assert response.status == HTTPStatus.CREATED
                # return the event_id, which is the last item of the path
                event_id = response.headers[hdrs.LOCATION].split("/")[-1]

        # Add list of contestants to event:
        headers = {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        with open("tests/files/contestants_all.csv", "rb") as file:
            logging.debug(f"Adding contestants from file at url {url}.")
            async with session.post(url, headers=headers, data=file) as response:
                status = response.status
                body = await response.json()
                if response.status != HTTPStatus.OK:
                    body = await response.json()
                    logging.error(
                        f"Got unexpected status {response.status}, reason {body}."
                    )
                assert status == HTTPStatus.OK

        # Generate raceclasses based on contestants:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/generate-raceclasses"
        )
        async with session.post(url, headers=headers) as response:
            assert response.status == HTTPStatus.CREATED
            assert f"/events/{event_id}/raceclasses" in response.headers[hdrs.LOCATION]

        # Set group and order on all raceclasses:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses"
        )
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceclasses = await response.json()
            for raceclass in raceclasses:
                raceclass_id = raceclass["id"]
                (
                    raceclass["group"],
                    raceclass["order"],
                    raceclass["ranking"],
                ) = await _decide_group_order_and_ranking(raceclass)
                async with session.put(
                    f"{url}/{raceclass_id}", headers=headers, json=raceclass
                ) as put_response:
                    assert put_response.status == HTTPStatus.NO_CONTENT

        # Then we have to assign bibs to all contestants:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            assert response.status == HTTPStatus.CREATED
            assert f"/events/{event_id}/contestants" in response.headers[hdrs.LOCATION]

        # Get the contestants for debugging purposes:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK

        # We need to base the startlist on the raceplan. Need to generate it.
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != HTTPStatus.CREATED:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
            assert response.status == HTTPStatus.CREATED
        # Get the raceplan for debugging purposes:
        url = f"{http_service}/raceplans?eventId={event_id}"
        async with session.get(url) as response:
            if response.status != HTTPStatus.OK:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
            assert response.status == HTTPStatus.OK
            _raceplans = await response.json()
        # We generate the startlist:
        request_body = {"event_id": event_id}
        url = f"{http_service}/startlists/generate-startlist-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != HTTPStatus.CREATED:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
            assert response.status == HTTPStatus.CREATED, body
            assert "/startlists/" in response.headers[hdrs.LOCATION]

        return _raceplans[0]


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_create_raceplan(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return 405 Method not allowed."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = json.dumps(context, indent=4, sort_keys=True, default=str)

    session = ClientSession()
    async with session.post(url, headers=headers, data=request_body) as response:
        status = response.status
    await session.close()

    assert status == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_raceplans(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return OK and a list of raceplans as json."""
    url = f"{http_service}/raceplans"

    session = ClientSession()
    async with session.get(url) as response:
        raceplans = await response.json()
    await session.close()

    assert response.status == HTTPStatus.OK
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceplans) is list
    assert len(raceplans) > 0


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_raceplan_by_event_id(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return OK and a list with one raceplan as json."""
    event_id = context["event_id"]

    url = f"{http_service}/raceplans?eventId={event_id}"
    session = ClientSession()
    async with session.get(url) as response:
        raceplans = await response.json()
    await session.close()

    assert response.status == HTTPStatus.OK
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceplans) is list
    assert len(raceplans) == 1
    assert raceplans[0]["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_raceplan(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return OK and an raceplan as json."""
    url = f"{http_service}/raceplans"

    raceplan_id = context["id"]
    url = f"{url}/{raceplan_id}"

    async with ClientSession() as session, session.get(url) as response:
        raceplan = await response.json()

    assert response.status == HTTPStatus.OK
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceplan) is dict
    assert raceplan["id"] == raceplan_id
    assert raceplan["event_id"] == context["event_id"]
    for i, race in enumerate(raceplan["races"]):
        assert race["id"] == context["races"][i]


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_validate_raceplan(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return 200 OK and and a body with a list of results."""
    raceplan_id = context["id"]
    url = f"{http_service}/raceplans/{raceplan_id}/validate"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    session = ClientSession()
    async with session.post(url, headers=headers) as response:
        status = response.status
        results = await response.json()
    await session.close()

    assert status == HTTPStatus.OK
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(results) is dict
    assert len(results) == 0


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_update_race(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return No Content."""
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    races = context["races"]
    race_to_be_updated_id = races[-1]  # we update the last race

    url = f"{http_service}/races/{race_to_be_updated_id}"

    async with ClientSession() as session:
        async with session.get(url) as response:
            race_to_be_updated = await response.json()
        # we change the start-time:
        race_to_be_updated["start_time"] = "2021-12-06T11:00:00"
        request_body = json.dumps(
            race_to_be_updated, indent=4, sort_keys=True, default=str
        )
        async with session.put(url, headers=headers, data=request_body) as response:
            pass

        assert response.status == HTTPStatus.NO_CONTENT

        # We get all the races in event to verify:
        url = f"{http_service}/races?eventId={context['event_id']}"
        async with session.get(url, headers=headers, data=request_body) as response:
            _ = await response.json()

        assert response.status == HTTPStatus.OK


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_update_raceplan(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    raceplan_id = context["id"]
    url = f"{url}/{raceplan_id}"
    update_raceplan = deepcopy(context)
    update_raceplan["event_id"] = "new_event_id"
    request_body = json.dumps(update_raceplan, indent=4, sort_keys=True, default=str)
    async with (
        ClientSession() as session,
        session.put(url, headers=headers, data=request_body) as response,
    ):
        pass

    assert response.status == HTTPStatus.NO_CONTENT


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_delete_raceplan(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            raceplans = await response.json()
        raceplan_id = raceplans[0]["id"]
        url = f"{url}/{raceplan_id}"
        async with session.delete(url, headers=headers) as response:
            pass

    assert response.status == HTTPStatus.NO_CONTENT


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_raceplan_by_event_id_when_event_does_not_exist(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return OK and an empty list."""
    event_id = "does_not_exist"
    url = f"{http_service}/raceplans?eventId={event_id}"

    session = ClientSession()
    async with session.get(url) as response:
        raceplans = await response.json()
    await session.close()

    assert response.status == HTTPStatus.OK
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(raceplans) is list
    assert len(raceplans) == 0


# ---
async def _decide_group_order_and_ranking(  # noqa: C901
    raceclass: dict,
) -> tuple[int, int, bool]:
    if raceclass["name"] == "MS":
        return (1, 1, True)
    if raceclass["name"] == "KS":
        return (1, 2, True)
    if raceclass["name"] == "M19-20":
        return (1, 3, True)
    if raceclass["name"] == "K19-20":
        return (1, 4, True)
    if raceclass["name"] == "M18":
        return (2, 1, True)
    if raceclass["name"] == "K18":
        return (2, 2, True)
    if raceclass["name"] == "M17":
        return (3, 1, True)
    if raceclass["name"] == "K17":
        return (3, 2, True)
    if raceclass["name"] == "G16":
        return (4, 1, True)
    if raceclass["name"] == "J16":
        return (4, 2, True)
    if raceclass["name"] == "G15":
        return (4, 3, True)
    if raceclass["name"] == "J15":
        return (4, 4, True)
    if raceclass["name"] == "G14":
        return (5, 1, True)
    if raceclass["name"] == "J14":
        return (5, 2, True)
    if raceclass["name"] == "G13":
        return (5, 3, True)
    if raceclass["name"] == "J13":
        return (5, 4, True)
    if raceclass["name"] == "G12":
        return (6, 1, True)
    if raceclass["name"] == "J12":
        return (6, 2, True)
    if raceclass["name"] == "G11":
        return (6, 3, True)
    if raceclass["name"] == "J11":
        return (6, 4, True)
    if raceclass["name"] == "G10":
        return (7, 1, False)
    if raceclass["name"] == "J10":
        return (7, 2, False)
    if raceclass["name"] == "G9":
        return (8, 1, False)
    if raceclass["name"] == "J9":
        return (8, 2, False)
    return (0, 0, True)  # should not reach this point
