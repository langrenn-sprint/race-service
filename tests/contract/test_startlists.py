"""Contract test cases for startlists."""

import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
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

# ARRANGE


@pytest.fixture(scope="module", autouse=True)
async def token(http_service: Any) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {"Content-Type": "application/json"}
    request_startlist = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_startlist)
        startlist = response.json()

    if response.status_code != HTTPStatus.OK:
        logger.error(
            f"Got unexpected status {response.status_code} from {http_service}."
        )
    assert response.status_code == HTTPStatus.OK

    return startlist["token"]


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


@pytest.fixture(scope="module", autouse=True)
async def context(
    http_service: Any, token: MockFixture, clear_db: Any
) -> dict[str, str | list]:
    """Arrange and create startlist to do tests on."""
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
            request_startlist = competition_format
            response = await client.post(url, headers=headers, json=request_startlist)
            if response.status_code != HTTPStatus.CREATED:
                startlist = response.json()
                logger.error(f"When creating competition-format, got error {startlist}")
            assert response.status_code == HTTPStatus.CREATED

        # Next we create the event:
        with open("tests/files/event_individual_sprint.json") as file:
            event = json.load(file)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
            request_startlist = event
            response = await client.post(url, headers=headers, json=request_startlist)
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
            startlist = response.json()
            if response.status_code != HTTPStatus.OK:
                startlist = response.json()
                logger.error(
                    f"Got unexpected status {response.status_code}, reason {startlist}."
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
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants/assign-bibs"
        response = await client.post(url, headers=headers)
        assert response.status_code == HTTPStatus.CREATED
        assert f"/events/{event_id}/contestants" in response.headers["Location"]

        # Get the contestants for debugging purposes:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        contestants = response.json()

        # We need to base the startlist on the raceplan. Need to generate it.
        request_startlist = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        response = await client.post(url, headers=headers, json=request_startlist)
        if response.status_code != HTTPStatus.CREATED:
            startlist = response.json()
            logger.error(
                f"Got unexpected status {response.status_code}, reason {startlist}."
            )
        assert response.status_code == HTTPStatus.CREATED
        # Get the raceplan for debugging purposes:
        url = f"{http_service}/raceplans?eventId={event_id}"
        response = await client.get(url)
        if response.status_code != HTTPStatus.OK:
            startlist = response.json()
            logger.error(
                f"Got unexpected status {response.status_code}, reason {startlist}."
            )
        assert response.status_code == HTTPStatus.OK

        # Finally, we are ready to generate the startlist:
        request_startlist = {"event_id": event_id}
        url = f"{http_service}/startlists/generate-startlist-for-event"
        response = await client.post(url, headers=headers, json=request_startlist)
        if response.status_code != HTTPStatus.CREATED:
            startlist = response.json()
            logger.error(
                f"Got unexpected status {response.status_code}, reason {startlist}."
            )
        assert response.status_code == HTTPStatus.CREATED
        startlist_url = response.headers["Location"]
        assert "/startlists/" in startlist_url

        context: dict[str, str | list] = {
            "event_id": event_id,
            "startlist_url": startlist_url,
            "contestants": contestants,
        }
        return context


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_create_startlist_should_fail(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return 405 Method Not Allowed."""
    # ACT
    url = f"{http_service}/startlists"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_startlist = {"event_id": context["event_id"]}
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_startlist)
        response.json()

    # ASSERT
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_generate_startlist_when_event_already_has_one(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return 400 Bad request and error message in startlist."""
    # ACT
    url = f"{http_service}/startlists/generate-startlist-for-event"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    request_startlist = {"event_id": context["event_id"]}
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_startlist)
        startlist = response.json()

    # ASSERT
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        f'Event "{context["event_id"]}" already has a startlist.' == startlist["detail"]
    )


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_startlists(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return OK and a list of startlists as json."""
    # ACT

    url = f"{http_service}/startlists"

    async with AsyncClient() as client:
        response = await client.get(url)
        startlists = response.json()

    # ASSERT

    assert response.status_code == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
    assert type(startlists) is list
    assert len(startlists) == 1


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_startlist_by_event_id(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return OK and a list with one startlist as json."""
    # ACT
    event_id = context["event_id"]
    startlist_id = context["startlist_url"].split("/")[-1]
    url = f"{http_service}/startlists?eventId={event_id}"

    async with AsyncClient() as client:
        response = await client.get(url)
        startlists = response.json()

    # ASSERT

    assert response.status_code == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
    assert type(startlists) is list
    assert len(startlists) == 1
    assert startlists[0]["id"] == startlist_id
    assert startlists[0]["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_startlist(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return OK and an startlist as json."""
    # ACT
    url = context["startlist_url"]
    async with AsyncClient() as client:
        response = await client.get(url)
        startlist = response.json()

    # ASSERT

    assert response.status_code == HTTPStatus.OK
    assert type(startlist) is dict
    assert startlist["id"] == context["startlist_url"].split("/")[-1]
    assert startlist["event_id"] == context["event_id"]
    assert startlist["start_entries"]
    # TODO: Adjust this test to take non-ranked classes and both rounds into account:
    # assert len(startlist["start_entries"]) == len(context["contestants"])
    bibs = [contestant["bib"] for contestant in context["contestants"]]
    for start_entry in startlist["start_entries"]:
        assert "race_id" in start_entry
        assert start_entry["bib"] in bibs
        assert "starting_position" in start_entry
        assert "scheduled_start_time" in start_entry


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_add_start_entry_to_race_first_round(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return 204 No content and add start_entry to the race, raceplan and the startlist."""
    # ARRANGE

    startlist_id = context["startlist_url"].split("/")[-1]

    headers = {
        "Authorization": f"Bearer {token}",
    }
    async with AsyncClient() as client:
        # Need to get to a race to be the new start-entry in:
        url = f"{http_service}/races?eventId={context['event_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        races = response.json()
        assert len(races) > 0

        # We add the new contestant to the first race:
        race = races[0]

        # Existing start-entries:
        url = f"{http_service}/races/{race['id']}/start-entries"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        existing_start_entries = response.json()

        startlist_id = context["startlist_url"].split("/")[-1]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        startlist = response.json()

        # We need to get the raceplan:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan = response.json()

        # ACT

        # We add the new start-entry to the race:
        new_start_entry = {
            "startlist_id": startlist["id"],
            "race_id": race["id"],
            "bib": 9999,
            "starting_position": len(existing_start_entries) + 1,
            "scheduled_start_time": race["start_time"],
            "name": "New Contestant",
            "club": "The always late to attend club",
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        request_body = json.dumps(
            new_start_entry, indent=4, sort_keys=True, default=str
        )

        url = f"{http_service}/races/{race['id']}/start-entries"
        response = await client.post(url, headers=headers, content=request_body)
        try:
            body = response.json()
        except json.JSONDecodeError:
            body = None

        # ASSERT

        assert response.status_code == HTTPStatus.CREATED, (
            f"body:{body}" if body else ""
        )
        assert f"/races/{race['id']}/start-entries/" in response.headers["Location"]

        # Check that the start-entry is in the list of start-entries of the race:
        new_start_entry_id = response.headers["Location"].split("/")[-1]

        url = f"{http_service}/races/{race['id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        race_updated = response.json()
        assert race["no_of_contestants"] + 1 == race_updated["no_of_contestants"]
        assert len(race["start_entries"]) + 1 == len(race_updated["start_entries"])
        assert new_start_entry_id in [
            start_entry["id"] for start_entry in race_updated["start_entries"]
        ]

        # Check that the start-entry is in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        startlist_updated = response.json()
        assert (
            startlist_updated["no_of_contestants"] == startlist["no_of_contestants"] + 1
        )
        assert new_start_entry_id in [
            start_entry["id"] for start_entry in startlist_updated["start_entries"]
        ]

        # Since the race is in first round, check that raceplan's no_of_contestants is updated:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan_updated = response.json()
        assert (
            raceplan_updated["no_of_contestants"] == raceplan["no_of_contestants"] + 1
        )


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_add_start_entry_to_race_not_first_round(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return 204 No content and add start_entry to the race and the startlist."""
    # ARRANGE

    startlist_id = context["startlist_url"].split("/")[-1]

    headers = {
        "Authorization": f"Bearer {token}",
    }
    async with AsyncClient() as client:
        # Need to get to a race to be the new start-entry in:
        url = f"{http_service}/races?eventId={context['event_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        races = response.json()
        assert len(races) > 0

        # We add the new contestant to the last race:
        race = races[-1]

        # Existing start-entries:
        url = f"{http_service}/races/{race['id']}/start-entries"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        existing_start_entries = response.json()

        startlist_id = context["startlist_url"].split("/")[-1]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        startlist = response.json()

        # We need to get the raceplan:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan = response.json()

        # ACT

        # We add the new start-entry to the race:
        new_start_entry = {
            "startlist_id": startlist["id"],
            "race_id": race["id"],
            "bib": 9999,
            "starting_position": len(existing_start_entries) + 1,
            "scheduled_start_time": race["start_time"],
            "name": "New Contestant",
            "club": "The always late to attend club",
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        request_body = json.dumps(
            new_start_entry, indent=4, sort_keys=True, default=str
        )

        url = f"{http_service}/races/{race['id']}/start-entries"
        response = await client.post(url, headers=headers, content=request_body)
        try:
            body = response.json()
        except json.JSONDecodeError:
            body = None

        # ASSERT

        assert response.status_code == HTTPStatus.CREATED, (
            f"body:{body}" if body else ""
        )
        assert f"/races/{race['id']}/start-entries/" in response.headers["Location"]

        new_start_entry_id = response.headers["Location"].split("/")[-1]

        # Check that the start-entry is in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        startlist_updated = response.json()
        assert (
            startlist_updated["no_of_contestants"] == startlist["no_of_contestants"] + 1
        )
        assert new_start_entry_id in [
            start_entry["id"] for start_entry in startlist_updated["start_entries"]
        ]

        # Since the race is in not first round, check that raceplan's no_of_contestants is not updated:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan_updated = response.json()
        assert raceplan_updated["no_of_contestants"] == raceplan["no_of_contestants"]


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_remove_start_entry_from_race_first_round(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return 204 No content and remove start_entry from the race, raceplan and the startlist."""
    # ARRANGE

    startlist_id = context["startlist_url"].split("/")[-1]

    headers = {
        "Authorization": f"Bearer {token}",
    }
    async with AsyncClient() as client:
        # Need to get to a race:
        url = f"{http_service}/races"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        races = response.json()
        assert len(races) > 0
        # Pick the first race, which is in the first round:
        race = races[0]
        assert len(race["start_entries"]) > 0

        url = f"{http_service}/races/{race['id']}/start-entries"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        start_entries = response.json()
        assert len(start_entries) > 0
        start_entry_to_be_removed = start_entries[0]

        assert startlist_id == start_entry_to_be_removed["startlist_id"]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        startlist = response.json()

        # We need to get the raceplan:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan = response.json()

        # ACT

        # We remove the start-entry from the race:
        start_entry_id = start_entry_to_be_removed["id"]
        url = f"{http_service}/races/{race['id']}/start-entries/{start_entry_id}"
        response = await client.delete(url, headers=headers)

        # ASSERT

        assert response.status_code == HTTPStatus.NO_CONTENT

        # Check that the start-entry is no longer in the list of start-entries of the race:
        url = f"{http_service}/races/{race['id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        race_updated = response.json()
        assert race["no_of_contestants"] - 1 == race_updated["no_of_contestants"]
        assert len(race["start_entries"]) - 1 == len(race_updated["start_entries"])
        assert start_entry_id not in race_updated["start_entries"]

        # Check that the start-entry is no longer in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        startlist_updated = response.json()
        assert (
            startlist_updated["no_of_contestants"] == startlist["no_of_contestants"] - 1
        )
        assert start_entry_id not in startlist_updated["start_entries"]

        # Check that raceplan's no_of_contestants is updated:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan_updated = response.json()
        assert (
            raceplan_updated["no_of_contestants"] == raceplan["no_of_contestants"] - 1
        )


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_remove_start_entry_from_race_not_first_round(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return 204 No content and remove start_entry from the race and the startlist."""
    # ARRANGE

    startlist_id = context["startlist_url"].split("/")[-1]

    headers = {
        "Authorization": f"Bearer {token}",
    }
    async with AsyncClient() as client:
        # Need to get to a race:
        url = f"{http_service}/races"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        races = response.json()
        assert len(races) > 0
        # We pick the last race, which is not in the first round:
        race = races[-1]
        assert len(race["start_entries"]) > 0

        url = f"{http_service}/races/{race['id']}/start-entries"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        start_entries = response.json()
        assert len(start_entries) > 0
        start_entry_to_be_removed = start_entries[0]

        assert startlist_id == start_entry_to_be_removed["startlist_id"]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        startlist = response.json()

        # We need to get the raceplan:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan = response.json()

        # ACT

        # We remove the start-entry from the race:
        start_entry_id = start_entry_to_be_removed["id"]
        url = f"{http_service}/races/{race['id']}/start-entries/{start_entry_id}"
        response = await client.delete(url, headers=headers)

        # ASSERT

        assert response.status_code == HTTPStatus.NO_CONTENT

        # Check that the start-entry is no longer in the list of start-entries of the race:
        url = f"{http_service}/races/{race['id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        race_updated = response.json()
        assert race["no_of_contestants"] - 1 == race_updated["no_of_contestants"]
        assert len(race["start_entries"]) - 1 == len(race_updated["start_entries"])
        assert start_entry_id not in race_updated["start_entries"]

        # Check that the start-entry is no longer in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        startlist_updated = response.json()
        assert (
            startlist_updated["no_of_contestants"] == startlist["no_of_contestants"] - 1
        )
        assert start_entry_id not in startlist_updated["start_entries"]

        # Check that raceplan's no_of_contestants is not updated:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan_updated = response.json()
        assert raceplan_updated["no_of_contestants"] == raceplan["no_of_contestants"]


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_update_startlist(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return 405 Not allowed."""
    # ARRANGE
    url = context["startlist_url"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers,
        )
        assert response.status_code == HTTPStatus.OK
        startlist_to_be_updated = response.json()

        # ACT

        startlist_to_be_updated["event_id"] = str(uuid.uuid4())

        request_startlist = json.dumps(
            startlist_to_be_updated, indent=4, sort_keys=True, default=str
        )
        response = await client.put(url, headers=headers, content=request_startlist)

    # ASSERT

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_delete_startlist(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return No Content."""
    # ACT

    url = context["startlist_url"]
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.delete(url, headers=headers)

        # ASSERT

        assert response.status_code == HTTPStatus.NO_CONTENT

        # Inspect start-entries in races. They should be gone.
        url = f"{http_service}/races?eventId={context['event_id']}"

        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        races = response.json()
        for race in races:
            assert len(race["start_entries"]) == 0, (
                f"Race has still got start-entries: {race}"
            )


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_get_all_startlists_by_event_id_when_event_does_not_exist(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return OK and an empty list."""
    # ARRANGE

    event_id = str(uuid.uuid4())  # an event that does not exist

    # ACT

    url = f"{http_service}/startlists?eventId={event_id}"

    async with AsyncClient() as client:
        response = await client.get(url)
        startlists = response.json()

    # ASSERT

    assert response.status_code == HTTPStatus.OK
    assert "application/json" in response.headers["Content-Type"]
    assert type(startlists) is list
    assert len(startlists) == 0


# ---


async def delete_competition_formats(token: MockFixture) -> None:
    """Delete all competition_formats."""
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        competition_formats = response.json()
        for competition_format in competition_formats:
            delete_response = await client.delete(
                f"{url}/{competition_format['id']}", headers=headers
            )
            assert delete_response.status_code == HTTPStatus.NO_CONTENT
    logger.info("Clear_db: Deleted all competition_formats.")


async def delete_events(token: MockFixture) -> None:
    """Delete all events."""
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        events = response.json()
        for event in events:
            delete_response = await client.delete(
                f"{url}/{event['id']}", headers=headers
            )
            assert delete_response.status_code == HTTPStatus.NO_CONTENT
    logger.info("Clear_db: Deleted all events.")


async def delete_contestants(token: MockFixture) -> None:
    """Delete all contestants."""
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        events = response.json()
        for event in events:
            delete_response = await client.delete(
                f"{url}/{event['id']}/contestants", headers=headers
            )
            assert delete_response.status_code == HTTPStatus.NO_CONTENT
    logger.info("Clear_db: Deleted all contestants.")


async def delete_raceclasses(token: MockFixture) -> None:
    """Delete all raceclasses."""
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        events = response.json()
        for event in events:
            get_response = await client.get(
                f"{url}/{event['id']}/raceclasses", headers=headers
            )
            assert get_response.status_code == HTTPStatus.OK
            raceclasses = get_response.json()
            for raceclass in raceclasses:
                delete_response = await client.delete(
                    f"{url}/{event['id']}/raceclasses/{raceclass['id']}",
                    headers=headers,
                )
                assert delete_response.status_code == HTTPStatus.NO_CONTENT
    logger.info("Clear_db: Deleted all raceclasses.")


async def delete_raceplans(http_service: Any, token: MockFixture) -> None:
    """Delete all raceplans."""
    url = f"{http_service}/raceplans"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplans = response.json()
        for raceplan in raceplans:
            raceplan_id = raceplan["id"]
            delete_response = await client.delete(
                f"{url}/{raceplan_id}", headers=headers
            )
            assert delete_response.status_code == HTTPStatus.NO_CONTENT
    logger.info("Clear_db: Deleted all raceplans.")


async def delete_startlists(http_service: Any, token: MockFixture) -> None:
    """Delete all startlists including start-entries."""
    url = f"{http_service}/startlists"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        startlists = response.json()
        for startlist in startlists:
            startlist_id = startlist["id"]
            delete_response = await client.delete(
                f"{url}/{startlist_id}", headers=headers
            )
            assert delete_response.status_code == HTTPStatus.NO_CONTENT
    logger.info("Clear_db: Deleted all startlists.")


async def delete_start_entries(http_service: Any, token: MockFixture) -> None:
    """Delete all start_entries."""
    url = f"{http_service}/races"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with AsyncClient() as client:
        response = await client.get(url)
        races = response.json()
        for race in races:
            race_id = race["id"]
            for start_entry_id in race["start_entries"]:
                delete_response = await client.delete(
                    f"{url}/{race_id}/start-entries/{start_entry_id}",
                    headers=headers,
                )
                assert delete_response.status_code == HTTPStatus.NO_CONTENT
    logger.info("Clear_db: Deleted all start_entries.")
