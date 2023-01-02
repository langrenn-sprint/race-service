"""Contract test cases for time-events."""
import asyncio
from copy import deepcopy
import json
import logging
import os
from typing import Any, AsyncGenerator, Tuple

from aiohttp import ClientSession, hdrs
import motor.motor_asyncio
import pytest
from pytest_mock import MockFixture


EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT")
COMPETITION_FORMAT_HOST_SERVER = os.getenv("COMPETITION_FORMAT_HOST_SERVER")
COMPETITION_FORMAT_HOST_PORT = os.getenv("COMPETITION_FORMAT_HOST_PORT")
USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 27017))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


@pytest.fixture(scope="module", autouse=True)
def event_loop(request: Any) -> Any:
    """Redefine the event_loop fixture to have the same scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
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
    mongo = motor.motor_asyncio.AsyncIOMotorClient(
        host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASSWORD
    )
    try:
        await mongo.drop_database(f"{DB_NAME}")
    except Exception as error:
        logging.error(f"Failed to drop database {DB_NAME}: {error}")
        raise error
    logging.info(" --- Testing starts. ---")
    yield
    logging.info(" --- Testing finished. ---")
    logging.info(" --- Cleaning db after testing. ---")
    try:
        await mongo.drop_database(f"{DB_NAME}")
    except Exception as error:
        logging.error(f"Failed to drop database {DB_NAME}: {error}")
        raise error
    logging.info(" --- Cleaning db done. ---")


@pytest.fixture(scope="module", autouse=True)
@pytest.mark.asyncio
async def set_up_context(http_service: Any, token: MockFixture, clear_db: Any) -> dict:
    """Create context and return event_id."""
    event_id = ""
    async with ClientSession() as session:
        # First we need create the competition-format:
        with open("tests/files/competition_format_individual_sprint.json", "r") as file:
            competition_format = json.load(file)
            headers = {
                hdrs.CONTENT_TYPE: "application/json",
                hdrs.AUTHORIZATION: f"Bearer {token}",
            }
            url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"  # noqa: B950
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
        files = {"file": open("tests/files/contestants_all.csv", "rb")}
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
                (
                    raceclass["group"],
                    raceclass["order"],
                    raceclass["ranking"],
                ) = await _decide_group_order_and_ranking(raceclass)
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
    async with ClientSession() as session:
        url = f"{http_service}/races/{race_id}/start-entries"
        async with session.get(url) as response:
            assert response.status == 200
            start_entries = await response.json()

    return {
        "bib": start_entries[0]["bib"],  # we pick the first start-entry in the race
        "event_id": raceplan["event_id"],
        "name": "Petter Propell",
        "club": "Barnehagen",
        "race_id": race_id,
        "race": "race_name",
        "timing_point": "Finish",
        "rank": 1,
        "registration_time": "12:01:02",
        "next_race_id": "semi_1",
        "next_race_position": 1,
        "status": "",
        "changelog": None,
    }


@pytest.mark.contract
@pytest.mark.asyncio
async def test_create_time_event(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return 201 Created, location header and no body."""
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = json.dumps(new_time_event, indent=4, sort_keys=True, default=str)
    async with ClientSession() as session:
        url = f"{http_service}/time-events"
        async with session.post(url, headers=headers, data=request_body) as response:
            assert response.status == 200, "POST of new_time_event failed."
            body = await response.json()
            assert body["status"] == "OK"

        # We check that the race has a race_result for the given timing point:
        url = f'{http_service}/races/{new_time_event["race_id"]}'
        async with session.get(url) as response:
            assert response.status == 200, "GET of race failed."
            race = await response.json()
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
@pytest.mark.asyncio
async def test_create_same_time_event(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return 400 Bad request."""
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    request_body = json.dumps(new_time_event, indent=4, sort_keys=True, default=str)
    async with ClientSession() as session:
        url = f"{http_service}/time-events"
        async with session.post(url, headers=headers, data=request_body) as response:
            assert (
                response.status == 400
            ), "POST of new_time_event succeeded, should have failed."


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_time_events(http_service: Any, token: MockFixture) -> None:
    """Should return OK and a list of time_events as json."""
    url = f"{http_service}/time-events"

    async with ClientSession() as session:
        async with session.get(url) as response:
            assert response.status == 200
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            time_events = await response.json()
        assert type(time_events) is list
        assert len(time_events) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_time_events_by_event_id(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and a list with one time_event as json."""
    event_id = new_time_event["event_id"]
    url = f"{http_service}/time-events?eventId={event_id}"

    async with ClientSession() as session:
        async with session.get(url) as response:
            assert response.status == 200
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            time_events = await response.json()

        assert type(time_events) is list
        assert len(time_events) == 1
        assert time_events[0]["event_id"] == event_id


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_time_event(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and an time_event as json."""
    url = f"{http_service}/time-events"

    async with ClientSession() as session:
        async with session.get(url) as response:
            time_events = await response.json()
        id = time_events[0]["id"]
        url = f"{url}/{id}"
        async with session.get(url) as response:
            assert response.status == 200
            time_event = await response.json()

        assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
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
@pytest.mark.asyncio
async def test_update_time_event(http_service: Any, token: MockFixture) -> None:
    """Should return No Content."""
    url = f"{http_service}/time-events"
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url) as response:
            assert response.status == 200
            time_events = await response.json()

        id = time_events[0]["id"]
        url = f"{url}/{id}"
        update_time_event = deepcopy(time_events[0])
        update_time_event["event_id"] = "new_event_id"
        request_body = json.dumps(
            update_time_event, indent=4, sort_keys=True, default=str
        )
        async with session.put(url, headers=headers, data=request_body) as response:
            assert response.status == 204


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_time_event(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return No Content."""
    url = f"{http_service}/time-events"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }
    async with ClientSession() as session:
        async with session.get(url) as response:
            time_events = await response.json()
        time_event = time_events[0]
        time_event_id = time_event["id"]
        url = f"{url}/{time_event_id}"
        async with session.delete(url, headers=headers) as response:
            assert response.status == 204

        # We check if the time_event is removed from the corresponding race-result:
        url = f'{http_service}/races/{time_event["race_id"]}/race-results'
        async with session.get(url) as response:
            body = await response.json()
            assert (
                response.status == 200
            ), f'status={response.status}, detail={body["detail"]}'
            race_results = body
            race_result = race_results[0]
            assert time_event_id not in race_result["ranking_sequence"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_time_event_by_event_id_when_event_does_not_exist(
    http_service: Any, token: MockFixture, new_time_event: dict
) -> None:
    """Should return OK and an empty list."""
    event_id = "does_not_exist"
    url = f"{http_service}/time-events?eventId={event_id}"

    async with ClientSession() as session:
        async with session.get(url) as response:
            assert response.status == 200
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            time_events = await response.json()

        assert type(time_events) is list
        assert len(time_events) == 0


# ---
async def _decide_group_order_and_ranking(  # noqa: C901
    raceclass: dict,
) -> Tuple[int, int, bool]:
    if raceclass["name"] == "M19/20":
        return (1, 1, True)
    elif raceclass["name"] == "K19/20":
        return (1, 2, True)
    elif raceclass["name"] == "M18":
        return (2, 1, True)
    elif raceclass["name"] == "K18":
        return (2, 2, True)
    elif raceclass["name"] == "M17":
        return (3, 1, True)
    elif raceclass["name"] == "K17":
        return (3, 2, True)
    elif raceclass["name"] == "G16":
        return (4, 1, True)
    elif raceclass["name"] == "J16":
        return (4, 2, True)
    elif raceclass["name"] == "G15":
        return (4, 3, True)
    elif raceclass["name"] == "J15":
        return (4, 4, True)
    elif raceclass["name"] == "G14":
        return (5, 1, True)
    elif raceclass["name"] == "J14":
        return (5, 2, True)
    elif raceclass["name"] == "G13":
        return (5, 3, True)
    elif raceclass["name"] == "J13":
        return (5, 4, True)
    elif raceclass["name"] == "G12":
        return (6, 1, True)
    elif raceclass["name"] == "J12":
        return (6, 2, True)
    elif raceclass["name"] == "G11":
        return (6, 3, True)
    elif raceclass["name"] == "J11":
        return (6, 4, True)
    elif raceclass["name"] == "G10":
        return (7, 1, False)
    elif raceclass["name"] == "J10":
        return (7, 2, False)
    elif raceclass["name"] == "G9":
        return (8, 1, False)
    elif raceclass["name"] == "J9":
        return (8, 2, False)
    return (0, 0, True)  # should not reach this point
