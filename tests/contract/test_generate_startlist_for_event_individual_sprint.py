"""Contract test cases for command generate-startlist-for-event."""

import json
import logging
import os
from collections.abc import AsyncGenerator
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

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
async def token(http_service: Any) -> str:
    """Create a valid token."""
    url = f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/login"
    headers = {hdrs.CONTENT_TYPE: "application/json"}
    request_body = {
        "username": os.getenv("ADMIN_USERNAME"),
        "password": os.getenv("ADMIN_PASSWORD"),
    }
    async with (
        ClientSession() as session,
        session.post(url, headers=headers, json=request_body) as response,
    ):
        assert response.status == HTTPStatus.OK
        body = await response.json()
        if response.status != HTTPStatus.OK:
            logger.error(
                f"Got unexpected status {response.status} from {http_service}."
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


@pytest.fixture(scope="module")
async def expected_startlist() -> dict:
    """Create a mock startlist object."""
    with open("tests/files/expected_startlist_individual_sprint.json") as file:
        return json.load(file)


# Finally we test the test_generate_startlist_for_event function:
@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_generate_startlist_for_individual_sprint_event(
    http_service: Any,
    token: MockFixture,
    expected_startlist: dict,
    clear_db: Any,
) -> None:
    """Should return 201 created and a location header with url to startlist."""
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
                    logger.error(f"When creating competition-format, got error {body}")
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
            logger.debug(f"Adding contestants from file at url {url}.")
            async with session.post(url, headers=headers, data=file) as response:
                status = response.status
                no_of_contestants_added = await response.json()
                if response.status != HTTPStatus.OK:
                    body = await response.json()
                    logger.error(
                        f"Got unexpected status {response.status}, reason {body}."
                    )
                assert status == HTTPStatus.OK

        # Get the contestants for debugging purposes:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            _contestants = await response.json()

        assert no_of_contestants_added["created"] == len(_contestants)

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
        await _print_raceclasses(raceclasses)

        # Then we have to assign bibs to all contestants:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            assert response.status == HTTPStatus.CREATED
            assert f"/events/{event_id}/contestants" in response.headers[hdrs.LOCATION]

        # Get the contestants for debugging purposes:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            _contestants = await response.json()

        await _print_contestants(_contestants)

        # We need to base the startlist on the raceplan. Need to generate it.
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != HTTPStatus.CREATED:
                body = await response.json()
                logger.error(f"Got unexpected status {response.status}, reason {body}.")
            assert response.status == HTTPStatus.CREATED
            assert "/raceplans/" in response.headers[hdrs.LOCATION]
        # Get the raceplan for debugging purposes:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            if response.status != HTTPStatus.OK:
                body = await response.json()
                logger.error(f"Got unexpected status {response.status}, reason {body}.")
            assert response.status == HTTPStatus.OK
            raceplan = await response.json()

        # Sanity-check the raceplan
        assert raceplan["no_of_contestants"] == len(_contestants)
        await _print_raceplan(raceplan)

        # Finally, we are ready to generate the startlist:
        request_body = {"event_id": event_id}
        url = f"{http_service}/startlists/generate-startlist-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != HTTPStatus.CREATED:
                body = await response.json()
                logger.error(f"Got unexpected status {response.status}, reason {body}.")
            assert response.status == HTTPStatus.CREATED
            assert "/startlists/" in response.headers[hdrs.LOCATION]

        # We check that startlist is actually created:
        startlist_id = response.headers[hdrs.LOCATION].split("/")[-1]
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            startlist = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(startlist) is dict
            assert startlist["id"]
            assert startlist["event_id"] == request_body["event_id"]
            assert startlist["no_of_contestants"] == len(_contestants)

            await _print_startlist(startlist)
            await _dump_startlist_to_json(startlist)

            # And we compare the response to the expected startlist:
            assert (
                startlist["no_of_contestants"]
                == expected_startlist["no_of_contestants"]
            )
            assert len(startlist["start_entries"]) == len(
                expected_startlist["start_entries"]
            )

            for i, start_entry in enumerate(startlist["start_entries"]):
                expected_start_entry = expected_startlist["start_entries"][i]
                assert start_entry["bib"] == expected_start_entry["bib"], (
                    f'"bib" in index {i}:{start_entry}\n ne:\n{expected_start_entry}'
                )
                assert (
                    start_entry["starting_position"]
                    == expected_start_entry["starting_position"]
                ), (
                    f'"starting_position" in index {i}:{start_entry}\n ne:\n{expected_start_entry}'
                )
                assert (
                    start_entry["scheduled_start_time"]
                    == expected_start_entry["scheduled_start_time"]
                ), (
                    f'"scheduled_start_time" in index {i}:{start_entry}\n ne:\n{expected_start_entry}'
                )

        # We also need to check that all the relevant races has got a list of start_entries:
        url = f"{http_service}/races?eventId={request_body['event_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            races = await response.json()
            no_of_contestants = 0
            for race in [race for race in races if race["round"] in ["Q", "R1"]]:
                assert len(race["start_entries"]) > 0, (
                    f"race with round/order {race['order']}/{race['round']} does not have start_entries"
                )
                no_of_contestants += len(race["start_entries"])

                # We also check that the start_entries are sorted by starting_position:
                url = f"{http_service}/races/{race['id']}/start-entries"
                async with session.get(url) as start_entries_response:
                    assert start_entries_response.status == HTTPStatus.OK
                    start_entries = await start_entries_response.json()
                _starting_position: list[int] = [
                    start_entry["starting_position"] for start_entry in start_entries
                ]
                assert all(
                    _starting_position[i] <= _starting_position[i + 1]
                    for i in range(len(_starting_position) - 1)
                )

                assert len(race["start_entries"]) <= race["max_no_of_contestants"]
                assert race["no_of_contestants"] <= race["max_no_of_contestants"]
            assert no_of_contestants == startlist["no_of_contestants"]

        # We inspect one of the start_entries in the list of races:
        start_entry = races[0]["start_entries"][0]
        assert type(start_entry) is str

        # We inspect the details of the first race, which should include the whole start_entry object:
        url = f"{http_service}/races/{races[0]['id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            race = await response.json()
            assert race["no_of_contestants"] == len(race["start_entries"])
            for start_entry in race["start_entries"]:
                assert type(start_entry) is dict
                assert start_entry["id"]
                assert start_entry["startlist_id"] == startlist_id
                assert start_entry["race_id"] == race["id"]
                assert start_entry["bib"]
                assert start_entry["name"]
                assert start_entry["club"]
                assert start_entry["starting_position"]
                assert start_entry["scheduled_start_time"] == race["start_time"]


# ---
async def _decide_group_order_and_ranking(  # noqa: C901
    raceclass: dict,
) -> tuple[int, int, bool]:
    if raceclass["name"] == "Menn senior":
        return (1, 1, True)
    if raceclass["name"] == "Kvinner senior":
        return (1, 2, True)
    if raceclass["name"] == "Menn 19-20":
        return (1, 3, True)
    if raceclass["name"] == "Kvinner 19-20":
        return (1, 4, True)
    if raceclass["name"] == "Menn 18":
        return (2, 1, True)
    if raceclass["name"] == "Kvinner 18":
        return (2, 2, True)
    if raceclass["name"] == "Menn 17":
        return (3, 1, True)
    if raceclass["name"] == "Kvinner 17":
        return (3, 2, True)
    if raceclass["name"] == "G 16 år":
        return (4, 1, True)
    if raceclass["name"] == "J 16 år":
        return (4, 2, True)
    if raceclass["name"] == "G 15 år":
        return (4, 3, True)
    if raceclass["name"] == "J 15 år":
        return (4, 4, True)
    if raceclass["name"] == "G 14 år":
        return (5, 1, True)
    if raceclass["name"] == "J 14 år":
        return (5, 2, True)
    if raceclass["name"] == "G 13 år":
        return (5, 3, True)
    if raceclass["name"] == "J 13 år":
        return (5, 4, True)
    if raceclass["name"] == "G 12 år":
        return (6, 1, True)
    if raceclass["name"] == "J 12 år":
        return (6, 2, True)
    if raceclass["name"] == "G 11 år":
        return (6, 3, True)
    if raceclass["name"] == "J 11 år":
        return (6, 4, True)
    if raceclass["name"] == "G 10 år":
        return (7, 1, False)
    if raceclass["name"] == "J 10 år":
        return (7, 2, False)
    if raceclass["name"] == "G 9 år":
        return (8, 1, False)
    if raceclass["name"] == "J 9 år":
        return (8, 2, False)
    return (0, 0, True)  # should not reach this point


async def _print_raceclasses(raceclasses: list[dict]) -> None:
    print("--- raceclassES ---")
    print("group;order;name;ageclasses;no_of_contestants;ranking;distance;event_id")
    for raceclass in raceclasses:
        print(
            str(raceclass["group"])
            + ";"
            + str(raceclass["order"])
            + ";"
            + raceclass["name"]
            + ";"
            + "".join(raceclass["ageclasses"])
            + ";"
            + str(raceclass["no_of_contestants"])
            + ";"
            + str(raceclass["ranking"])
            + ";"
            + str(raceclass["distance"])
            + ";"
            + raceclass["event_id"]
        )


async def _print_raceplan(raceplan: dict) -> None:
    # print("--- RACEPLAN ---")
    # print(f'event_id: {raceplan["event_id"]}')
    # print(f'no_of_contestants: {raceplan["no_of_contestants"]}')
    # print("order;start_time;raceclass;round;index;heat;no_of_contestants")
    # for race in raceplan["races"]:
    #     print(
    #         str(race["order"])
    #         + ";"
    #         + str(race["start_time"])
    #         + ";"
    #         + str(race["raceclass"])
    #         + ";"
    #         + str(race["round"])
    #         + ";"
    #         + str(race["index"])
    #         + ";"
    #         + str(race["heat"])
    #         + ";"
    #         + str(race["no_of_contestants"])
    #     )
    pass


async def _print_contestants(contestants: list[dict]) -> None:
    # print("--- CONTESTANTS ---")
    # print(f"Number of contestants: {len(contestants)}.")
    # print("bib;ageclass;name")
    # for contestant in contestants:
    #     print(
    #         f'{contestant["bib"]};{contestant["ageclass"]};'
    #         f'{contestant["last_name"]}, {contestant["first_name"]}'
    #     )
    pass


async def _print_startlist(startlist: dict) -> None:
    # print("--- STARTLIST ---")
    # print(f'event_id: {startlist["event_id"]}')
    # print(f'no_of_contestants: {startlist["no_of_contestants"]}')
    # print("race_id;bib;starting_position;scheduled_start_time")
    # for start_entry in startlist["start_entries"]:
    #     print(
    #         str(start_entry["race_id"])
    #         + ";"
    #         + str(start_entry["bib"])
    #         + ";"
    #         + str(start_entry["starting_position"])
    #         + ";"
    #         + str(start_entry["scheduled_start_time"])
    #     )
    pass


async def _dump_startlist_to_json(startlist: dict) -> None:
    with open("tests/files/tmp_startlist_individual_sprint.json", "w") as file:
        json.dump(startlist, file, ensure_ascii=False)
