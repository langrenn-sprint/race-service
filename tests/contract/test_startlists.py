"""Contract test cases for startlists."""

import json
import logging
import os
from collections.abc import AsyncGenerator
from http import HTTPStatus
from typing import Any

import motor.motor_asyncio
import pytest
from aiohttp import ClientSession, ContentTypeError, hdrs
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

# ARRANGE


@pytest.fixture(scope="module", autouse=True)
async def token(http_service: Any) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {hdrs.CONTENT_TYPE: "application/json"}
    request_startlist = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    async with (
        ClientSession() as session,
        session.post(url, headers=headers, json=request_startlist) as response,
    ):
        startlist = await response.json()

    if response.status != HTTPStatus.OK:
        logging.error(f"Got unexpected status {response.status} from {http_service}.")
    assert response.status == HTTPStatus.OK

    return startlist["token"]


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


@pytest.fixture(scope="module", autouse=True)
async def context(
    http_service: Any, token: MockFixture, clear_db: Any
) -> dict[str, str | list]:
    """Arrange and create startlist to do tests on."""
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
            request_startlist = competition_format
            async with session.post(
                url, headers=headers, json=request_startlist
            ) as response:
                if response.status != HTTPStatus.CREATED:
                    startlist = await response.json()
                    logging.error(
                        f"When creating competition-format, got error {startlist}"
                    )
                assert response.status == HTTPStatus.CREATED

        # Next we create the event:
        with open("tests/files/event_individual_sprint.json") as file:
            event = json.load(file)

            headers = {
                hdrs.CONTENT_TYPE: "application/json",
                hdrs.AUTHORIZATION: f"Bearer {token}",
            }
            url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
            request_startlist = event
            async with session.post(
                url, headers=headers, json=request_startlist
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
                startlist = await response.json()
                if response.status != HTTPStatus.OK:
                    startlist = await response.json()
                    logging.error(
                        f"Got unexpected status {response.status}, reason {startlist}."
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
                _id = raceclass["id"]
                (
                    raceclass["group"],
                    raceclass["order"],
                    raceclass["ranking"],
                ) = await _decide_group_order_and_ranking(raceclass)
                async with session.put(
                    f"{url}/{_id}", headers=headers, json=raceclass
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
            contestants = await response.json()

        # We need to base the startlist on the raceplan. Need to generate it.
        request_startlist = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(
            url, headers=headers, json=request_startlist
        ) as response:
            if response.status != HTTPStatus.CREATED:
                startlist = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {startlist}."
                )
            assert response.status == HTTPStatus.CREATED
        # Get the raceplan for debugging purposes:
        url = f"{http_service}/raceplans?eventId={event_id}"
        async with session.get(url) as response:
            if response.status != HTTPStatus.OK:
                startlist = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {startlist}."
                )
            assert response.status == HTTPStatus.OK

        # Finally, we are ready to generate the startlist:
        request_startlist = {"event_id": event_id}
        url = f"{http_service}/startlists/generate-startlist-for-event"
        async with session.post(
            url, headers=headers, json=request_startlist
        ) as response:
            if response.status != HTTPStatus.CREATED:
                startlist = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {startlist}."
                )
            assert response.status == HTTPStatus.CREATED
            startlist_url = response.headers[hdrs.LOCATION]
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
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_startlist = {"event_id": context["event_id"]}
    async with (
        ClientSession() as session,
        session.post(url, headers=headers, json=request_startlist) as response,
    ):
        await response.json()

    # ASSERT
    assert response.status == HTTPStatus.METHOD_NOT_ALLOWED


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
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_startlist = {"event_id": context["event_id"]}
    async with (
        ClientSession() as session,
        session.post(url, headers=headers, json=request_startlist) as response,
    ):
        startlist = await response.json()

    # ASSERT
    assert response.status == HTTPStatus.BAD_REQUEST
    assert (
        f'Event "{context["event_id"]!r}" already has a startlist.'
        == startlist["detail"]
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

    async with ClientSession() as session, session.get(url) as response:
        startlists = await response.json()

    # ASSERT

    assert response.status == HTTPStatus.OK
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
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

    async with ClientSession() as session, session.get(url) as response:
        startlists = await response.json()

    # ASSERT

    assert response.status == HTTPStatus.OK
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
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
    async with ClientSession() as session, session.get(url) as response:
        startlist = await response.json()

    # ASSERT

    assert response.status == HTTPStatus.OK
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
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    async with ClientSession() as session:
        # Need to get to a race to be the new start-entry in:
        url = f"{http_service}/races?eventId={context['event_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            races = await response.json()
            assert len(races) > 0

            # We add the new contestant to the first race:
            race = races[0]

        # Existing start-entries:
        url = f"{http_service}/races/{race['id']}/start-entries"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            existing_start_entries = await response.json()

        startlist_id = context["startlist_url"].split("/")[-1]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            startlist = await response.json()

        # We need to get the raceplan:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan = await response.json()

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
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        request_body = json.dumps(
            new_start_entry, indent=4, sort_keys=True, default=str
        )

        url = f"{http_service}/races/{race['id']}/start-entries"
        async with session.post(url, headers=headers, data=request_body) as response:
            try:
                body = await response.json()
            except ContentTypeError:
                body = None

        # ASSERT

        assert response.status == HTTPStatus.CREATED, f"body:{body}" if body else ""
        assert f"/races/{race['id']}/start-entries/" in response.headers[hdrs.LOCATION]

        # Check that the start-entry is in the list of start-entries of the race:
        new_start_entry_id = response.headers[hdrs.LOCATION].split("/")[-1]

        url = f"{http_service}/races/{race['id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            race_updated = await response.json()
            assert race["no_of_contestants"] + 1 == race_updated["no_of_contestants"]
            assert len(race["start_entries"]) + 1 == len(race_updated["start_entries"])
            assert new_start_entry_id in [
                start_entry["id"] for start_entry in race_updated["start_entries"]
            ]

        # Check that the start-entry is in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            startlist_updated = await response.json()
            assert (
                startlist_updated["no_of_contestants"]
                == startlist["no_of_contestants"] + 1
            )
            assert new_start_entry_id in [
                start_entry["id"] for start_entry in startlist_updated["start_entries"]
            ]

        # Since the race is in first round, check that raceplan's no_of_contestants is updated:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan_updated = await response.json()
            assert (
                raceplan_updated["no_of_contestants"]
                == raceplan["no_of_contestants"] + 1
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
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    async with ClientSession() as session:
        # Need to get to a race to be the new start-entry in:
        url = f"{http_service}/races?eventId={context['event_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            races = await response.json()
            assert len(races) > 0

            # We add the new contestant to the last race:
            race = races[-1]

        # Existing start-entries:
        url = f"{http_service}/races/{race['id']}/start-entries"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            existing_start_entries = await response.json()

        startlist_id = context["startlist_url"].split("/")[-1]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            startlist = await response.json()

        # We need to get the raceplan:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan = await response.json()

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
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        request_body = json.dumps(
            new_start_entry, indent=4, sort_keys=True, default=str
        )

        url = f"{http_service}/races/{race['id']}/start-entries"
        async with session.post(url, headers=headers, data=request_body) as response:
            try:
                body = await response.json()
            except ContentTypeError:
                body = None

        # ASSERT

        assert response.status == HTTPStatus.CREATED, f"body:{body}" if body else ""
        assert f"/races/{race['id']}/start-entries/" in response.headers[hdrs.LOCATION]

        new_start_entry_id = response.headers[hdrs.LOCATION].split("/")[-1]

        # Check that the start-entry is in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            startlist_updated = await response.json()
            assert (
                startlist_updated["no_of_contestants"]
                == startlist["no_of_contestants"] + 1
            )
            assert new_start_entry_id in [
                start_entry["id"] for start_entry in startlist_updated["start_entries"]
            ]

        # Since the race is in not first round, check that raceplan's no_of_contestants is not updated:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan_updated = await response.json()
            assert (
                raceplan_updated["no_of_contestants"] == raceplan["no_of_contestants"]
            )


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
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    async with ClientSession() as session:
        # Need to get to a race:
        url = f"{http_service}/races"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            races = await response.json()
            assert len(races) > 0
            # Pick the first race, which is in the first round:
            race = races[0]
            assert len(race["start_entries"]) > 0

        url = f"{http_service}/races/{race['id']}/start-entries"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            start_entries = await response.json()
            assert len(start_entries) > 0
            start_entry_to_be_removed = start_entries[0]

        assert startlist_id == start_entry_to_be_removed["startlist_id"]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            startlist = await response.json()

        # We need to get the raceplan:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan = await response.json()

        # ACT

        # We remove the start-entry from the race:
        start_entry_id = start_entry_to_be_removed["id"]
        url = f"{http_service}/races/{race['id']}/start-entries/{start_entry_id}"
        async with session.delete(url, headers=headers) as response:
            pass

        # ASSERT

        assert response.status == HTTPStatus.NO_CONTENT

        # Check that the start-entry is no longer in the list of start-entries of the race:
        url = f"{http_service}/races/{race['id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            race_updated = await response.json()
            assert race["no_of_contestants"] - 1 == race_updated["no_of_contestants"]
            assert len(race["start_entries"]) - 1 == len(race_updated["start_entries"])
            assert start_entry_id not in race_updated["start_entries"]

        # Check that the start-entry is no longer in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            startlist_updated = await response.json()
            assert (
                startlist_updated["no_of_contestants"]
                == startlist["no_of_contestants"] - 1
            )
            assert start_entry_id not in startlist_updated["start_entries"]

        # Check that raceplan's no_of_contestants is updated:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan_updated = await response.json()
            assert (
                raceplan_updated["no_of_contestants"]
                == raceplan["no_of_contestants"] - 1
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
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    async with ClientSession() as session:
        # Need to get to a race:
        url = f"{http_service}/races"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            races = await response.json()
            assert len(races) > 0
            # We pick the last race, which is not in the first round:
            race = races[-1]
            assert len(race["start_entries"]) > 0

        url = f"{http_service}/races/{race['id']}/start-entries"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            start_entries = await response.json()
            assert len(start_entries) > 0
            start_entry_to_be_removed = start_entries[0]

        assert startlist_id == start_entry_to_be_removed["startlist_id"]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            startlist = await response.json()

        # We need to get the raceplan:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan = await response.json()

        # ACT

        # We remove the start-entry from the race:
        start_entry_id = start_entry_to_be_removed["id"]
        url = f"{http_service}/races/{race['id']}/start-entries/{start_entry_id}"
        async with session.delete(url, headers=headers) as response:
            pass

        # ASSERT

        assert response.status == HTTPStatus.NO_CONTENT

        # Check that the start-entry is no longer in the list of start-entries of the race:
        url = f"{http_service}/races/{race['id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            race_updated = await response.json()
            assert race["no_of_contestants"] - 1 == race_updated["no_of_contestants"]
            assert len(race["start_entries"]) - 1 == len(race_updated["start_entries"])
            assert start_entry_id not in race_updated["start_entries"]

        # Check that the start-entry is no longer in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            startlist_updated = await response.json()
            assert (
                startlist_updated["no_of_contestants"]
                == startlist["no_of_contestants"] - 1
            )
            assert start_entry_id not in startlist_updated["start_entries"]

        # Check that raceplan's no_of_contestants is not updated:
        url = f"{http_service}/raceplans/{race['raceplan_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan_updated = await response.json()
            assert (
                raceplan_updated["no_of_contestants"] == raceplan["no_of_contestants"]
            )


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
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(
            url,
            headers=headers,
        ) as response:
            assert response.status == HTTPStatus.OK
            startlist_to_be_updated = await response.json()

        # ACT

        startlist_to_be_updated["event_id"] = "new_event_id"

        request_startlist = json.dumps(
            startlist_to_be_updated, indent=4, sort_keys=True, default=str
        )
        async with session.put(
            url, headers=headers, data=request_startlist
        ) as response:
            pass

    # ASSERT

    assert response.status == HTTPStatus.METHOD_NOT_ALLOWED


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
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            pass

        # ASSERT

        assert response.status == HTTPStatus.NO_CONTENT

        # Inspect start-entries in races. They should be gone.
        url = f"{http_service}/races?eventId={context['event_id']}"

        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            races = await response.json()
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

    event_id = "does_not_exist"

    # ACT

    url = f"{http_service}/startlists?eventId={event_id}"

    async with ClientSession() as session, session.get(url) as response:
        startlists = await response.json()

    # ASSERT

    assert response.status == HTTPStatus.OK
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(startlists) is list
    assert len(startlists) == 0


# ---


async def delete_competition_formats(token: MockFixture) -> None:
    """Delete all competition_formats."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            competition_formats = await response.json()
            for competition_format in competition_formats:
                async with session.delete(
                    f"{url}/{competition_format['id']}", headers=headers
                ) as delete_response:
                    assert delete_response.status == HTTPStatus.NO_CONTENT
    logging.info("Clear_db: Deleted all competition_formats.")


async def delete_events(token: MockFixture) -> None:
    """Delete all events."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            events = await response.json()
            for event in events:
                async with session.delete(
                    f"{url}/{event['id']}", headers=headers
                ) as delete_response:
                    assert delete_response.status == HTTPStatus.NO_CONTENT
    logging.info("Clear_db: Deleted all events.")


async def delete_contestants(token: MockFixture) -> None:
    """Delete all contestants."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            events = await response.json()
            for event in events:
                async with session.delete(
                    f"{url}/{event['id']}/contestants", headers=headers
                ) as delete_response:
                    assert delete_response.status == HTTPStatus.NO_CONTENT
    logging.info("Clear_db: Deleted all contestants.")


async def delete_raceclasses(token: MockFixture) -> None:
    """Delete all raceclasses."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            events = await response.json()
            for event in events:
                async with session.get(
                    f"{url}/{event['id']}/raceclasses", headers=headers
                ) as get_response:
                    assert get_response.status == HTTPStatus.OK
                    raceclasses = await get_response.json()
                    for raceclass in raceclasses:
                        async with session.delete(
                            f"{url}/{event['id']}/raceclasses/{raceclass['id']}",
                            headers=headers,
                        ) as delete_response:
                            assert delete_response.status == HTTPStatus.NO_CONTENT
    logging.info("Clear_db: Deleted all raceclasses.")


async def delete_raceplans(http_service: Any, token: MockFixture) -> None:
    """Delete all raceplans."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session, session.get(url) as response:
        assert response.status == HTTPStatus.OK
        raceplans = await response.json()
        for raceplan in raceplans:
            raceplan_id = raceplan["id"]
            async with session.delete(
                f"{url}/{raceplan_id}", headers=headers
            ) as delete_response:
                assert delete_response.status == HTTPStatus.NO_CONTENT
    logging.info("Clear_db: Deleted all raceplans.")


async def delete_startlists(http_service: Any, token: MockFixture) -> None:
    """Delete all startlists including start-entries."""
    url = f"{http_service}/startlists"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session, session.get(url) as response:
        assert response.status == HTTPStatus.OK
        startlists = await response.json()
        for startlist in startlists:
            startlist_id = startlist["id"]
            async with session.delete(
                f"{url}/{startlist_id}", headers=headers
            ) as delete_response:
                assert delete_response.status == HTTPStatus.NO_CONTENT
    logging.info("Clear_db: Deleted all startlists.")


async def delete_start_entries(http_service: Any, token: MockFixture) -> None:
    """Delete all start_entries."""
    url = f"{http_service}/races"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session, session.get(url) as response:
        races = await response.json()
        for race in races:
            race_id = race["id"]
            for start_entry_id in race["start_entries"]:
                async with session.delete(
                    f"{url}/{race_id}/start-entries/{start_entry_id}",
                    headers=headers,
                ) as delete_response:
                    assert delete_response.status == HTTPStatus.NO_CONTENT
    logging.info("Clear_db: Deleted all start_entries.")


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
