"""Contract test cases for startlists."""
import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Tuple, Union

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


# Arrange:


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def token(http_service: Any) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {hdrs.CONTENT_TYPE: "application/json"}
    request_startlist = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    async with ClientSession() as session:
        async with session.post(
            url, headers=headers, json=request_startlist
        ) as response:
            startlist = await response.json()

    if response.status != 200:
        logging.error(f"Got unexpected status {response.status} from {http_service}.")
    assert response.status == 200

    return startlist["token"]


@pytest.fixture(scope="module", autouse=True)
@pytest.mark.asyncio
async def clear_db(http_service: Any, token: MockFixture) -> AsyncGenerator:
    """Clear db before and after tests."""
    logging.info(" --- Cleaning db at startup. ---")
    await delete_startlists(http_service, token)
    await delete_raceplans(http_service, token)
    await delete_contestants(token)
    await delete_raceclasses(token)
    await delete_events(token)
    await delete_competition_formats(token)
    logging.info(" --- Testing starts. ---")
    yield
    logging.info(" --- Testing finished. ---")
    logging.info(" --- Cleaning db after testing. ---")
    await delete_start_entries(http_service, token)
    await delete_startlists(http_service, token)
    await delete_raceplans(http_service, token)
    await delete_contestants(token)
    await delete_raceclasses(token)
    await delete_events(token)
    await delete_competition_formats(token)
    logging.info(" --- Cleaning db done. ---")


@pytest.fixture(scope="module", autouse=True)
@pytest.mark.asyncio
async def context(http_service: Any, token: MockFixture) -> Dict[str, Union[str, List]]:
    """Arrange and create startlist to do tests on."""
    event_id = ""
    async with ClientSession() as session:
        # First we need create the competition-format:
        with open("tests/files/competition_format_individual_sprint.json", "r") as file:
            competition_format = json.load(file)
            headers = {
                hdrs.CONTENT_TYPE: "application/json",
                hdrs.AUTHORIZATION: f"Bearer {token}",
            }
            url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats"
            request_startlist = competition_format
            async with session.post(
                url, headers=headers, json=request_startlist
            ) as response:
                if response.status != 201:
                    startlist = await response.json()
                    logging.error(
                        f"When creating competition-format, got error {startlist}"
                    )
                assert response.status == 201

        # Next we create the event:
        with open("tests/files/event_individual_sprint.json", "r") as file:
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
                assert response.status == 201
                # return the event_id, which is the last item of the path
                event_id = response.headers[hdrs.LOCATION].split("/")[-1]

        # Add list of contestants to event:
        headers = {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        files = {"file": open("tests/files/all_contestants_eventid_364892.csv", "rb")}
        logging.debug(f"Adding contestants from file at url {url}.")
        async with session.post(url, headers=headers, data=files) as response:
            status = response.status
            startlist = await response.json()
            if response.status != 200:
                startlist = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {startlist}."
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

        # Set group and order on all raceclasses:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses"
        )
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceclasses = await response.json()
            for raceclass in raceclasses:
                id = raceclass["id"]
                raceclass["group"], raceclass["order"] = await _decide_group_and_order(
                    raceclass
                )
                async with session.put(
                    f"{url}/{id}", headers=headers, json=raceclass
                ) as response:
                    assert response.status == 204

        # Then we have to assign bibs to all contestants:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/contestants" in response.headers[hdrs.LOCATION]

        # Get the contestants for debugging purposes:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            contestants = await response.json()

        # We need to base the startlist on the raceplan. Need to generate it.
        request_startlist = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(
            url, headers=headers, json=request_startlist
        ) as response:
            if response.status != 201:
                startlist = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {startlist}."
                )
            assert response.status == 201
        # Get the raceplan for debugging purposes:
        url = f"{http_service}/raceplans?eventId={event_id}"
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                startlist = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {startlist}."
                )
            assert response.status == 200

        # Finally, we are ready to generate the startlist:
        request_startlist = {"event_id": event_id}
        url = f"{http_service}/startlists/generate-startlist-for-event"
        async with session.post(
            url, headers=headers, json=request_startlist
        ) as response:
            if response.status != 201:
                startlist = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {startlist}."
                )
            assert response.status == 201
            startlist_url = response.headers[hdrs.LOCATION]
            assert "/startlists/" in startlist_url

        context: Dict[str, Union[str, List]] = {
            "event_id": event_id,
            "startlist_url": startlist_url,
            "contestants": contestants,
        }
        return context


@pytest.mark.contract
@pytest.mark.asyncio
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
    async with ClientSession() as session:
        async with session.post(
            url, headers=headers, json=request_startlist
        ) as response:
            await response.json()

    # ASSERT
    assert response.status == 405


@pytest.mark.contract
@pytest.mark.asyncio
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
    async with ClientSession() as session:
        async with session.post(
            url, headers=headers, json=request_startlist
        ) as response:
            startlist = await response.json()

    # ASSERT
    assert response.status == 400
    assert (
        f'Event "{context["event_id"]}" already has a startlist.' == startlist["detail"]
    )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_startlists(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return OK and a list of startlists as json."""
    # ACT

    url = f"{http_service}/startlists"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            startlists = await response.json()

    # ASSERT

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(startlists) is list
    assert len(startlists) == 1


@pytest.mark.contract
@pytest.mark.asyncio
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
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            startlists = await response.json()

    # ASSERT

    assert response.status == 200
    assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
    assert type(startlists) is list
    assert len(startlists) == 1
    assert startlists[0]["id"] == startlist_id
    assert startlists[0]["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_startlist(
    http_service: Any,
    token: MockFixture,
    context: dict,
) -> None:
    """Should return OK and an startlist as json."""
    # ACT
    url = f"{http_service}/startlists"

    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    url = context["startlist_url"]
    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            startlist = await response.json()

    # ASSERT

    assert response.status == 200
    assert type(startlist) is dict
    assert startlist["id"] == context["startlist_url"].split("/")[-1]
    assert startlist["event_id"] == context["event_id"]
    assert startlist["start_entries"]
    assert len(startlist["start_entries"]) == len(context["contestants"])
    bibs = [contestant["bib"] for contestant in context["contestants"]]
    for start_entry in startlist["start_entries"]:
        assert "race_id" in start_entry
        assert start_entry["bib"] in bibs
        assert "starting_position" in start_entry
        assert "scheduled_start_time" in start_entry


@pytest.mark.contract
@pytest.mark.asyncio
async def test_add_start_entry_to_race(
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
        # Need to get to a race to be the new start-entry in:
        url = f'{http_service}/races?eventId={context["event_id"]}'
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            races = await response.json()
            assert len(races) > 0

            # Find the first race that is not a quarter-final:
            race = next(race for race in races if race["round"] != "Q")

            assert len(race["start_entries"]) == 0

        # Existing start-entries:
        url = f'{http_service}/races/{race["id"]}/start-entries'
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            existing_start_entries = await response.json()
            assert len(existing_start_entries) == 0

        startlist_id = context["startlist_url"].split("/")[-1]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            startlist = await response.json()

        # ACT

        # We add the new start-entry to the race:
        new_start_entry = {
            "startlist_id": startlist["id"],
            "race_id": race["id"],
            "bib": 1,
            "starting_position": 1,
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

        url = f'{http_service}/races/{race["id"]}/start-entries'
        async with session.post(url, headers=headers, data=request_body) as response:
            if response.status != 201:
                body = await response.json()

        # ASSERT

        assert response.status == 201, f"Reason: {body}"
        assert f'/races/{race["id"]}/start-entries/' in response.headers[hdrs.LOCATION]

        # Check that the start-entry is in the list of start-entries of the race:
        new_start_entry_id = response.headers[hdrs.LOCATION].split("/")[-1]

        url = f'{http_service}/races/{race["id"]}'
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            race_updated = await response.json()
            assert new_start_entry_id in [
                start_entry["id"] for start_entry in race_updated["start_entries"]
            ]

        # Check that the start-entry is in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            startlist_updated = await response.json()
            assert (
                startlist_updated["no_of_contestants"]
                == startlist["no_of_contestants"] + 1
            )
            assert new_start_entry_id in [
                start_entry["id"] for start_entry in startlist_updated["start_entries"]
            ]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_remove_start_entry_from_race(
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
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            races = await response.json()
            assert len(races) > 0
            race = races[0]
            assert len(race["start_entries"]) > 0

        url = f'{http_service}/races/{race["id"]}/start-entries'
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            start_entries = await response.json()
            assert len(start_entries) > 0
            start_entry_to_be_removed = start_entries[0]

        assert startlist_id == start_entry_to_be_removed["startlist_id"]

        # We need to get the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            startlist = await response.json()

        # ACT

        # We remove the start-entry from the race:
        start_entry_id = start_entry_to_be_removed["id"]
        url = f'{http_service}/races/{race["id"]}/start-entries/{start_entry_id}'
        async with session.delete(url, headers=headers) as response:
            pass

        # ASSERT

        assert response.status == 204

        # Check that the start-entry is no longer in the list of start-entries of the race:
        url = f'{http_service}/races/{race["id"]}'
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            race_updated = await response.json()
            assert start_entry_id not in race_updated["start_entries"]

        # Check that the start-entry is no longer in the list of start-entries of the startlist:
        url = f"{http_service}/startlists/{startlist_id}"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            startlist_updated = await response.json()
            assert (
                startlist_updated["no_of_contestants"]
                == startlist["no_of_contestants"] - 1
            )
            assert start_entry_id not in startlist_updated["start_entries"]


@pytest.mark.contract
@pytest.mark.asyncio
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
            assert response.status == 200
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

    assert response.status == 405


@pytest.mark.contract
@pytest.mark.asyncio
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

        assert response.status == 204

        # Inspect start-entries in races. They should be gone.
        url = f'{http_service}/races?eventId={context["event_id"]}'

        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            races = await response.json()
            for race in races:
                assert (
                    len(race["start_entries"]) == 0
                ), f"Race has still got start-entries: {race}"


@pytest.mark.contract
@pytest.mark.asyncio
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
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            startlists = await response.json()

    # ASSERT

    assert response.status == 200
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
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            competition_formats = await response.json()
            for competition_format in competition_formats:
                async with session.delete(
                    f'{url}/{competition_format["id"]}', headers=headers
                ) as response:
                    assert response.status == 204
    logging.info("Clear_db: Deleted all competition_formats.")


async def delete_events(token: MockFixture) -> None:
    """Delete all events."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            events = await response.json()
            for event in events:
                async with session.delete(
                    f'{url}/{event["id"]}', headers=headers
                ) as response:
                    assert response.status == 204
    logging.info("Clear_db: Deleted all events.")


async def delete_contestants(token: MockFixture) -> None:
    """Delete all contestants."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            events = await response.json()
            for event in events:
                async with session.delete(
                    f'{url}/{event["id"]}/contestants', headers=headers
                ) as response:
                    assert response.status == 204
    logging.info("Clear_db: Deleted all contestants.")


async def delete_raceclasses(token: MockFixture) -> None:
    """Delete all raceclasses."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            events = await response.json()
            for event in events:
                async with session.get(
                    f'{url}/{event["id"]}/raceclasses', headers=headers
                ) as response:
                    assert response.status == 200
                    raceclasses = await response.json()
                    for raceclass in raceclasses:
                        async with session.delete(
                            f'{url}/{event["id"]}/raceclasses/{raceclass["id"]}',
                            headers=headers,
                        ) as response:
                            assert response.status == 204
    logging.info("Clear_db: Deleted all raceclasses.")


async def delete_raceplans(http_service: Any, token: MockFixture) -> None:
    """Delete all raceplans."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceplans = await response.json()
            for raceplan in raceplans:
                raceplan_id = raceplan["id"]
                async with session.delete(
                    f"{url}/{raceplan_id}", headers=headers
                ) as response:
                    assert response.status == 204
    logging.info("Clear_db: Deleted all raceplans.")


async def delete_startlists(http_service: Any, token: MockFixture) -> None:
    """Delete all startlists including start-entries."""
    url = f"{http_service}/startlists"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            startlists = await response.json()
            for startlist in startlists:
                startlist_id = startlist["id"]
                async with session.delete(
                    f"{url}/{startlist_id}", headers=headers
                ) as response:
                    assert response.status == 204
    logging.info("Clear_db: Deleted all startlists.")


async def delete_start_entries(http_service: Any, token: MockFixture) -> None:
    """Delete all start_entries."""
    url = f"{http_service}/races"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            races = await response.json()
            for race in races:
                race_id = race["id"]
                for start_entry_id in race["start_entries"]:
                    async with session.delete(
                        f"{url}/{race_id}/start-entries/{start_entry_id}",
                        headers=headers,
                    ) as response:
                        assert response.status == 204
    logging.info("Clear_db: Deleted all start_entries.")


async def _decide_group_and_order(raceclass: dict) -> Tuple[int, int]:  # noqa: C901
    if raceclass["name"] == "G16":  # race-order: 1
        return (1, 1)
    elif raceclass["name"] == "J16":  # race-order: 2
        return (1, 2)
    elif raceclass["name"] == "G15":  # race-order: 3
        return (1, 3)
    elif raceclass["name"] == "J15":  # race-order: 4
        return (1, 4)
    elif raceclass["name"] == "G14":  # race-order: 5
        return (2, 1)
    elif raceclass["name"] == "J14":  # race-order: 6
        return (2, 2)
    elif raceclass["name"] == "G13":  # race-order: 7
        return (2, 3)
    elif raceclass["name"] == "J13":  # race-order: 8
        return (2, 4)
    elif raceclass["name"] == "G12":  # race-order: 9
        return (3, 1)
    elif raceclass["name"] == "J12":  # race-order: 10
        return (3, 2)
    elif raceclass["name"] == "G11":  # race-order: 11
        return (3, 3)
    elif raceclass["name"] == "J11":  # race-order: 12
        return (3, 4)
    return (0, 0)  # should not reach this point
