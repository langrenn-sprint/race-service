"""Contract test cases for time-events."""

import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from copy import deepcopy
from http import HTTPStatus
from typing import Any

import pytest
from httpx import AsyncClient
from pymongo import AsyncMongoClient
from pytest_mock import MockFixture

from app.utils import db_utils

from .utils import _decide_group_order_and_ranking

DB_NAME = os.getenv("DB_NAME", "races_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
async def token(http_service: Any, users_url: str) -> str:
    """Create a valid token."""
    url = f"{users_url}/login"
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
async def clear_db(db_address: dict[str, Any]) -> AsyncGenerator:
    """Clear db before and after tests."""
    logger.info(" --- Cleaning db at startup. ---")
    mongo = AsyncMongoClient(**db_address, username=DB_USER, password=DB_PASSWORD)
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
    await mongo.close()


@pytest.fixture(scope="module", autouse=True)
async def set_up_context(
    http_service: Any,
    token: MockFixture,
    clear_db: Any,
    competition_format_url: str,
    events_url: str,
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
            url = f"{competition_format_url}/competition-formats"
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
            url = f"{events_url}/events"
            request_body = event
            response = await client.post(url, headers=headers, json=request_body)
            assert response.status_code == HTTPStatus.CREATED
            # return the event_id, which is the last item of the path
            event_id = response.headers["Location"].split("/")[-1]

        # Add list of contestants to event:
        headers = {
            "Authorization": f"Bearer {token}",
        }
        url = f"{events_url}/events/{event_id}/contestants/file"
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
        url = f"{events_url}/events/{event_id}/generate-raceclasses"
        response = await client.post(url, headers=headers)
        assert response.status_code == HTTPStatus.CREATED
        assert f"/events/{event_id}/raceclasses" in response.headers["Location"]

        # Set group and order on all raceclasses:
        url = f"{events_url}/events/{event_id}/raceclasses"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceclasses = response.json()
        for raceclass in raceclasses:
            _id = raceclass["id"]
            (
                raceclass["group"],
                raceclass["order"],
                raceclass["ranking"],
            ) = await _decide_group_order_and_ranking(raceclass)
            put_response = await client.put(
                f"{url}/{_id}", headers=headers, json=raceclass
            )
            assert put_response.status_code == HTTPStatus.NO_CONTENT

        # Then we have to assign bibs to all contestants:
        url = f"{events_url}/events/{event_id}/contestants/assign-bibs"
        response = await client.post(url, headers=headers)
        assert response.status_code == HTTPStatus.CREATED
        assert f"/events/{event_id}/contestants" in response.headers["Location"]

        # Get the contestants for debugging purposes:
        url = f"{events_url}/events/{event_id}/contestants"
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
        assert response.status_code == HTTPStatus.CREATED
        assert "/startlists/" in response.headers["Location"]

        return _raceplans[0]


@pytest.fixture(scope="module")
async def new_time_event(
    http_service: Any, token: MockFixture, set_up_context: dict
) -> dict:
    """Create a time_event object."""
    raceplan = set_up_context
    # We pick the first race to record the event on:
    race_id = raceplan["races"][0]
    # We need to find a valid bib in this particular race:
    async with AsyncClient() as client:
        url = f"{http_service}/races/{race_id}/start-entries"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        start_entries = response.json()

    return {
        "bib": start_entries[0]["bib"],  # we pick the first start-entry in the race
        "event_id": raceplan["event_id"],
        "name": "Petter Propell",
        "club": "Barnehagen",
        "race_id": race_id,
        "race": "race_name",
        "timing_point": "Finish",
        "rank": 1,
        "registration_time": "2023-02-11T12:01:02",
        "next_race_id": None,
        "next_race_position": 1,
        "status": "",
        "changelog": None,
    }


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_create_time_event(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return 201 Created, location header and no body."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = json.dumps(new_time_event, indent=4, sort_keys=True, default=str)
    async with AsyncClient() as client:
        url = f"{http_service}/time-events"
        response = await client.post(url, headers=headers, content=request_body)
        assert response.status_code == HTTPStatus.OK, "POST of new_time_event failed."
        body = response.json()
        assert body["status"] == "OK"

        # We check that the race has a race_result for the given timing point:
        url = f"{http_service}/races/{new_time_event['race_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK, "GET of race failed."
        race = response.json()
        assert type(race["results"]) is dict
        assert len(race["results"]) == 1
        assert "Finish" in race["results"]
        race_result = race["results"]["Finish"]
        assert type(race_result) is dict

        # We check that the new_timing_point is included in the race_result's ranking_sequence:
        assert "ranking_sequence" in race_result
        ranking_sequence = race_result["ranking_sequence"]
        assert type(ranking_sequence) is list
        assert len(ranking_sequence) == 1
        assert ranking_sequence[0]["bib"] == new_time_event["bib"]
        assert ranking_sequence[0]["event_id"] == new_time_event["event_id"]
        assert ranking_sequence[0]["timing_point"] == new_time_event["timing_point"]
        assert (
            ranking_sequence[0]["registration_time"]
            == new_time_event["registration_time"]
        )
        assert ranking_sequence[0]["race_id"] == new_time_event["race_id"]
        assert ranking_sequence[0]["status"] == "OK"


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_create_same_time_event(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return 400 Bad request."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_body = json.dumps(new_time_event, indent=4, sort_keys=True, default=str)
    async with AsyncClient() as client:
        url = f"{http_service}/time-events"
        response = await client.post(url, headers=headers, content=request_body)
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            "POST of new_time_event succeeded, should have failed."
        )


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_time_events(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of time_events as json."""
    url = f"{http_service}/time-events"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        time_events = response.json()
        assert type(time_events) is list
        assert len(time_events) > 0


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_time_events_by_event_id(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and a list with one time_event as json."""
    event_id = new_time_event["event_id"]
    url = f"{http_service}/time-events?eventId={event_id}"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        time_events = response.json()

        assert type(time_events) is list
        assert len(time_events) == 1
        assert time_events[0]["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_time_events_by_event_id_and_bib(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and a list with one time_event as json."""
    event_id = new_time_event["event_id"]
    bib = new_time_event["bib"]
    url = f"{http_service}/time-events?eventId={event_id}&bib={bib}"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        time_events = response.json()

        assert type(time_events) is list
        assert len(time_events) == 1
        assert time_events[0]["event_id"] == event_id
        assert time_events[0]["bib"] == bib


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_time_event(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and an time_event as json."""
    url = f"{http_service}/time-events"

    async with AsyncClient() as client:
        response = await client.get(url)
        time_events = response.json()
        _id = time_events[0]["id"]
        url = f"{url}/{_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        time_event = response.json()

        assert "application/json" in response.headers["Content-Type"]
        assert type(time_event) is dict
        assert time_event["id"]
        assert time_event["event_id"] == new_time_event["event_id"]
        assert time_event["race_id"] == new_time_event["race_id"]
        assert time_event["bib"] == new_time_event["bib"]
        assert time_event["timing_point"] == new_time_event["timing_point"]
        assert time_event["rank"] == new_time_event["rank"]
        assert time_event["registration_time"] == new_time_event["registration_time"]
        assert time_event["next_race_id"] == new_time_event["next_race_id"]
        assert time_event["next_race_position"] == new_time_event["next_race_position"]
        assert time_event["status"] == "OK"
        assert time_event["changelog"] == new_time_event["changelog"]


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_update_time_event(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/time-events"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        time_events = response.json()

        _id = time_events[0]["id"]
        url = f"{url}/{_id}"
        update_time_event = deepcopy(time_events[0])
        update_time_event["event_id"] = str(uuid.uuid4())
        request_body = json.dumps(
            update_time_event, indent=4, sort_keys=True, default=str
        )
        response = await client.put(url, headers=headers, content=request_body)
        assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_delete_time_event(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/time-events"
    headers = {
        "Authorization": f"Bearer {token}",
    }
    async with AsyncClient() as client:
        response = await client.get(url)
        time_events = response.json()
        time_event = time_events[0]
        time_event_id = time_event["id"]
        url = f"{url}/{time_event_id}"
        response = await client.delete(url, headers=headers)
        assert response.status_code == HTTPStatus.NO_CONTENT

        # We check if the time_event is removed from the corresponding race-result:
        url = f"{http_service}/races/{time_event['race_id']}/race-results"
        response = await client.get(url)
        body = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f"status={response.status_code}, detail={body['detail']}"
        )
        race_results = body
        race_result = race_results[0]
        assert time_event_id not in race_result["ranking_sequence"]


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_time_event_by_event_id_when_event_does_not_exist(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and an empty list."""
    event_id = str(uuid.uuid4())  # an event that does not exist
    url = f"{http_service}/time-events?eventId={event_id}"

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "application/json" in response.headers["Content-Type"]
        time_events = response.json()

        assert type(time_events) is list
        assert len(time_events) == 0


# ---
