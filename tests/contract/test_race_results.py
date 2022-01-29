"""Contract test cases for race-results."""
import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, Tuple

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
@pytest.mark.asyncio
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


@pytest.fixture(scope="module", autouse=True)
@pytest.mark.asyncio
async def clear_db(http_service: Any, token: MockFixture) -> AsyncGenerator:
    """Clear db before and after tests."""
    logging.info(" --- Cleaning db at startup. ---")
    await delete_race_results(http_service, token)
    await delete_time_events(http_service, token)
    await delete_start_entries(http_service, token)
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
    await delete_race_results(http_service, token)
    await delete_time_events(http_service, token)
    await delete_start_entries(http_service, token)
    await delete_startlists(http_service, token)
    await delete_raceplans(http_service, token)
    await delete_contestants(token)
    await delete_raceclasses(token)
    await delete_events(token)
    await delete_competition_formats(token)
    logging.info(" --- Cleaning db done. ---")


async def delete_competition_formats(token: MockFixture) -> None:
    """Delete all competition_formats."""
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats"
        async with session.get(url) as response:
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
        async with session.get(url) as response:
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
        async with session.get(url) as response:
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
        async with session.get(url) as response:
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
    """Delete all raceplans before we start."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
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
    """Delete all startlists before we start."""
    url = f"{http_service}/startlists"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
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
    """Delete all start_entries before we start."""
    url = f"{http_service}/races"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            races = await response.json()
            for race in races:
                race_id = race["id"]
                for start_entry_id in race["start_entries"]:
                    async with session.delete(
                        f"{url}/{race_id}/start-entries/{start_entry_id}",
                        headers=headers,
                    ) as response:
                        assert response.status == 204
    logging.info("Clear_db: Deleted all start-entries.")


async def delete_time_events(http_service: Any, token: MockFixture) -> None:
    """Delete all time_events before we start."""
    url = f"{http_service}/time-events"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            time_events = await response.json()
            for time_event in time_events:
                time_event_id = time_event["id"]
                async with session.delete(
                    f"{url}/{time_event_id}", headers=headers
                ) as response:
                    assert response.status == 204
    logging.info("Clear_db: Deleted all time-events.")


async def delete_race_results(http_service: Any, token: MockFixture) -> None:
    """Delete all race_results before we start."""
    url = f"{http_service}/races"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            races = await response.json()
            for race in races:
                race_id = race["id"]
                for timing_point in race["results"]:
                    async with session.delete(
                        f'{url}/{race_id}/race-results/{race["results"][timing_point]}',
                        headers=headers,
                    ) as response:
                        assert response.status == 204
    logging.info("Clear_db: Deleted all race-results.")


@pytest.fixture(scope="module", autouse=True)
@pytest.mark.asyncio
async def set_up_context(
    http_service: Any,
    token: MockFixture,
) -> str:
    """Create context and return url to time-event."""
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
            request_body = competition_format
            async with session.post(
                url, headers=headers, json=request_body
            ) as response:
                if response.status != 201:
                    body = await response.json()
                    logging.error(f"When creating competition-format, got error {body}")
                assert response.status == 201

        # Next we create the event:
        with open("tests/files/event_individual_sprint.json", "r") as file:
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
                assert response.status == 201
                # return the event_id, which is the last item of the path
                event_id = response.headers[hdrs.LOCATION].split("/")[-1]

        # Add list of contestants to event:
        headers = {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        files = {"file": open("tests/files/contestants_all_333.csv", "rb")}
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

        # Set group and order on all raceclasses:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses"
        )
        async with session.get(url) as response:
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
        async with session.get(url) as response:
            assert response.status == 200

        # We need to base the startlist on the raceplan. Need to generate it.
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 201:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
            assert response.status == 201
        # Get the raceplan for debugging purposes:
        url = f"{http_service}/raceplans?eventId={event_id}"
        async with session.get(url) as response:
            if response.status != 200:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
            assert response.status == 200
            _raceplans = await response.json()

        # We generate the startlist:
        request_body = {"event_id": event_id}
        url = f"{http_service}/startlists/generate-startlist-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 201:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
            assert response.status == 201
            assert "/startlists/" in response.headers[hdrs.LOCATION]

        raceplan = _raceplans[0]
        race_id = raceplan["races"][0]

        # We need to find a contestant that actually start in this race:
        url = f"{http_service}/races/{race_id}/start-entries"
        async with session.get(url) as response:
            assert response.status == 200
            start_entries = await response.json()

        new_time_event: dict = {
            "bib": start_entries[0]["bib"],
            "event_id": raceplan["event_id"],
            "race_id": race_id,
            "race": "race_name",
            "timing_point": "Finish",
            "rank": "1",
            "registration_time": "12:01:02",
            "next_race_id": "semi_1",
            "next_race_position": 1,
            "status": "",
            "changelog": None,
        }
        # And we add a time-event in order to create the race result.
        request_body = json.dumps(new_time_event, indent=4, sort_keys=True, default=str)
        url = f"{http_service}/time-events"
        async with session.post(url, headers=headers, data=request_body) as response:
            assert response.status == 201, "POST of new_time_event failed."
            assert (
                "/time-events/" in response.headers[hdrs.LOCATION]
            ), "Location header has wrong content."

        time_event_url = response.headers[hdrs.LOCATION]
        return time_event_url


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_race_result(
    http_service: Any, token: MockFixture, set_up_context: str
) -> None:
    """Should return 200 OK and a race result."""
    time_event_url = set_up_context
    async with ClientSession() as session:
        url = time_event_url
        async with session.get(url) as response:
            assert response.status == 200, "GET of new_time_event failed."
            time_event = await response.json()

        # We should be able to get race and its results:
        url = f'{http_service}/races/{time_event["race_id"]}'
        async with session.get(url) as response:
            assert response.status == 200, "GET of race-results failed."
            race = await response.json()
        assert type(race["results"]) is dict
        assert "Finish" in race["results"]
        assert len(race["results"]) == 1

        # We should be also be able to get race-results:
        url = f'{http_service}/races/{time_event["race_id"]}/race-results'
        async with session.get(url) as response:
            assert response.status == 200, "GET of race-results failed."
            race_results = await response.json()
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
        assert "OK" == time_event["status"]


# ---
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
