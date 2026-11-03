"""Contract test cases for raceplans."""

import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from copy import deepcopy
from http import HTTPStatus
from typing import Any

import motor.motor_asyncio
import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture

from app.utils import db_utils

from .utils import _decide_group_order_and_ranking

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

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
async def token(http_service: Any) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {"Content-Type": "application/json"}
    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    client = AsyncClient()
    response = await client.post(url, headers=headers, json=request_body)
    body = response.json()
    await client.aclose()
    if response.status_code != HTTPStatus.OK:
        logger.error(
            f"Got unexpected status {response.status_code} from {http_service}."
        )
    return body["token"]


@pytest.fixture(scope="module", autouse=True)
async def clear_db() -> AsyncGenerator:
    """Clear db before and after tests."""
    logger.info(" --- Cleaning db at startup. ---")
    mongo = motor.motor_asyncio.AsyncIOMotorClient(
        host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASSWORD
    )
    try:
        await db_utils.drop_db_and_recreate_indexes(mongo, DB_NAME)
    except Exception as error:
        logger.exception(f"Failed to drop database {DB_NAME}.")
        raise error from error
    logger.info(" --- Testing starts. ---")
    yield
    logger.info(" --- Testing finished. ---")
    logger.info(" --- Cleaning db after testing. ---")
    try:
        await db_utils.drop_db(mongo, DB_NAME)
    except Exception as error:
        logger.exception(f"Failed to drop database {DB_NAME}.")
        raise error from error
    logger.info(" --- Cleaning db done. ---")


# We create a context in which to test the RUD-functins
@pytest.fixture(scope="module", autouse=True)
async def context(
    http_service: Any,
    token: MockFixture,
    clear_db: Any,
) -> dict:
    """Create context and return event_id."""
    event_id = ""
    async with AsyncClient() as client:
        # First we need create the competition-format:
        with open("tests/files/competition_format_individual_sprint.json") as file:
            competition_format = json.load(file)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"
            request_body = competition_format
            response = await client.post(url, headers=headers, json=request_body)
            if response.status_code != HTTPStatus.CREATED:
                body = response.json()
                logger.error(f"When creating competition-format, got error {body}")
            assert response.status_code == HTTPStatus.CREATED

        # Next we create the event:
        with open("tests/files/event_individual_sprint.json") as file:
            event = json.load(file)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
            request_body = event
            response = await client.post(url, headers=headers, json=request_body)
            assert response.status_code == HTTPStatus.CREATED
            # return the event_id, which is the last item of the path
            event_id = response.headers["Location"].split("/")[-1]

        # Add list of contestants to event:
        headers = {
            "Authorization": f"Bearer {token}",
        }
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants/file"
        with open("tests/files/contestants_all.csv", "rb") as file:
            logger.debug(f"Adding contestants from file at url {url}.")
            response = await client.post(
                url, headers=headers, files={"file": (file.name, file, "text/csv")}
            )
            status = response.status_code
            body = response.json()
            if response.status_code != HTTPStatus.OK:
                body = response.json()
                logger.error(
                    f"Got unexpected status {response.status_code}, reason {body}."
                )
            assert status == HTTPStatus.OK

        # Generate raceclasses based on contestants:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/generate-raceclasses"
        )
        response = await client.post(url, headers=headers)
        assert response.status_code == HTTPStatus.CREATED
        assert f"/events/{event_id}/raceclasses" in response.headers["Location"]

        # Set group and order on all raceclasses:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses"
        )
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()
        for raceclass in raceclasses:
            raceclass_id = raceclass["id"]
            (
                raceclass["group"],
                raceclass["order"],
                raceclass["ranking"],
            ) = await _decide_group_order_and_ranking(raceclass)
            put_response = await client.put(
                f"{url}/{raceclass_id}", headers=headers, json=raceclass
            )
            assert put_response.status_code == HTTPStatus.NO_CONTENT

        # Then we have to assign bibs to all contestants:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants/assign-bibs"
        response = await client.post(url, headers=headers)
        assert response.status_code == HTTPStatus.CREATED
        assert f"/events/{event_id}/contestants" in response.headers["Location"]

        # Get the contestants for debugging purposes:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK

        # We need to base the startlist on the raceplan. Need to generate it.
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        response = await client.post(url, headers=headers, json=request_body)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
            logger.error(
                f"Got unexpected status {response.status_code}, reason {body}."
            )
        assert response.status_code == HTTPStatus.CREATED
        # Get the raceplan for debugging purposes:
        url = f"{http_service}/raceplans?eventId={event_id}"
        response = await client.get(url)
        if response.status_code != HTTPStatus.OK:
            body = response.json()
            logger.error(
                f"Got unexpected status {response.status_code}, reason {body}."
            )
        assert response.status_code == HTTPStatus.OK
        _raceplans = response.json()
        # We generate the startlist:
        request_body = {"event_id": event_id}
        url = f"{http_service}/startlists/generate-startlist-for-event"
        response = await client.post(url, headers=headers, json=request_body)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
            logger.error(
                f"Got unexpected status {response.status_code}, reason {body}."
            )
        assert response.status_code == HTTPStatus.CREATED, body
        assert "/startlists/" in response.headers["Location"]

        return _raceplans[0]


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_create_raceplan(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return 405 Method not allowed."""
    url = f"{http_service}/raceplans"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = json.dumps(context, indent=4, sort_keys=True, default=str)

    client = AsyncClient()
    response = await client.post(url, headers=headers, content=request_body)
    status = response.status_code
    await client.aclose()

    assert status == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_raceplans(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return OK and a list of raceplans as json."""
    url = f"{http_service}/raceplans"

    client = AsyncClient()
    response = await client.get(url)
    raceplans = response.json()
    await client.aclose()

    assert response.status_code == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
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
    client = AsyncClient()
    response = await client.get(url)
    raceplans = response.json()
    await client.aclose()

    assert response.status_code == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
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

    async with AsyncClient() as client:
        response = await client.get(url)
        raceplan = response.json()

    assert response.status_code == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
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
        "Authorization": f"Bearer {token}",
    }
    client = AsyncClient()
    response = await client.post(url, headers=headers)
    status = response.status_code
    results = response.json()
    await client.aclose()

    assert status == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
    assert type(results) is dict
    assert len(results) == 0


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_update_race(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return No Content."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    races = context["races"]
    race_to_be_updated_id = races[-1]  # we update the last race

    url = f"{http_service}/races/{race_to_be_updated_id}"

    async with AsyncClient() as client:
        response = await client.get(url)
        race_to_be_updated = response.json()
        # we change the start-time:
        race_to_be_updated["start_time"] = "2021-12-06T11:00:00"
        request_body = json.dumps(
            race_to_be_updated, indent=4, sort_keys=True, default=str
        )
        response = await client.put(url, headers=headers, content=request_body)

        assert response.status_code == HTTPStatus.NO_CONTENT

        # We get all the races in event to verify:
        url = f"{http_service}/races?eventId={context['event_id']}"
        response = await client.get(url, headers=headers)
        _ = response.json()

        assert response.status_code == HTTPStatus.OK


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_update_raceplan(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/raceplans"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    raceplan_id = context["id"]
    url = f"{url}/{raceplan_id}"
    update_raceplan = deepcopy(context)
    update_raceplan["event_id"] = str(uuid.uuid4())
    request_body = json.dumps(update_raceplan, indent=4, sort_keys=True, default=str)
    async with AsyncClient() as client:
        response = await client.put(url, headers=headers, content=request_body)

    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_delete_raceplan(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/raceplans"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        raceplans = response.json()
        raceplan_id = raceplans[0]["id"]
        url = f"{url}/{raceplan_id}"
        response = await client.delete(url, headers=headers)

    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_raceplan_by_event_id_when_event_does_not_exist(
    http_service: Any, token: MockFixture, context: dict
) -> None:
    """Should return OK and an empty list."""
    event_id = str(uuid.uuid4())  # an event that does not exist
    url = f"{http_service}/raceplans?eventId={event_id}"

    client = AsyncClient()
    response = await client.get(url)
    raceplans = response.json()
    await client.aclose()

    assert response.status_code == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
    assert type(raceplans) is list
    assert len(raceplans) == 0


# ---
