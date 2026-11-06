"""Contract test cases for race-results."""

import json
import logging
import os
from collections.abc import AsyncGenerator
from http import HTTPStatus
from typing import Any

import motor.motor_asyncio
import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture

from app.utils import db_utils

from .utils import _decide_group_order_and_ranking

DB_NAME = os.getenv("DB_NAME", "races_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

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
    mongo = motor.motor_asyncio.AsyncIOMotorClient(
        **db_address, username=DB_USER, password=DB_PASSWORD
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


@pytest.fixture(scope="module", autouse=True)
async def set_up_context(
    http_service: Any,
    token: MockFixture,
    clear_db: Any,
    competition_format_url: str,
    events_url: str,
) -> str:
    """Create context and return url to time-event."""
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

        raceplan = _raceplans[0]
        race_id = raceplan["races"][0]

        # We need to find a contestant that actually start in this race:
        url = f"{http_service}/races/{race_id}/start-entries"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        start_entries = response.json()

        new_time_event: dict = {
            "bib": start_entries[0]["bib"],
            "event_id": raceplan["event_id"],
            "race_id": race_id,
            "race": "race_name",
            "timing_point": "Finish",
            "rank": "1",
            "registration_time": "2023-02-11T12:01:02",
            "next_race_id": None,
            "next_race_position": 1,
            "status": "",
            "changelog": None,
        }
        # And we add a time-event in order to create the race result.
        request_body = json.dumps(new_time_event, indent=4, sort_keys=True, default=str)
        url = f"{http_service}/time-events"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        response = await client.post(url, headers=headers, content=request_body)
        assert response.status_code == HTTPStatus.OK, "POST of new_time_event failed."
        new_time_event = response.json()
        assert new_time_event["status"] == "OK"

        return f"{http_service}/time-events/{new_time_event['id']}"


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_race_result(
    http_service: Any, token: MockFixture, set_up_context: str
) -> None:
    """Should return 200 OK and a race result."""
    time_event_url = set_up_context
    async with AsyncClient() as client:
        url = time_event_url
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK, "GET of new_time_event failed."
        time_event = response.json()

        # We should be able to get race and its results:
        url = f"{http_service}/races/{time_event['race_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK, "GET of race-results failed."
        race = response.json()
        assert type(race["results"]) is dict
        assert "Finish" in race["results"]
        assert len(race["results"]) == 1

        # We should be also be able to get race-results:
        url = f"{http_service}/races/{time_event['race_id']}/race-results"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK, "GET of race-results failed."
        race_results = response.json()
        assert type(race_results) is list
        assert len(race_results) == 1

        # Inspect the race-result object:
        race_result = race_results[0]
        assert race_result["timing_point"] == "Finish"
        assert race_result["race_id"] == race["id"]
        assert race_result["no_of_contestants"] == 1

        # Inspect the timing-point object of the ranking-sequence:
        time_events = race_result["ranking_sequence"]
        assert type(time_events) is list
        time_event = time_events[0]
        time_event_id = time_event_url.split("/")[-1]
        assert time_event["id"] == time_event_id
        assert time_event["race_id"] == race["id"]
        assert time_event["status"] == "OK"


# ---
