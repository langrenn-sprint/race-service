"""Contract test cases for ping."""

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
DB_NAME = os.getenv("DB_NAME", "race_service_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
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
        logger.error(f"Got unexpected status {response.status} from {http_service}.")
    return body["token"]


@pytest.fixture(autouse=True)
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


@pytest.mark.contract
async def test_generate_raceplan_for_individual_sprint_event_all_1(
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
) -> None:
    """Should return 201 created and a location header with url to the raceplan."""
    # ARRANGE

    event_id = ""
    async with ClientSession() as session:
        # First we need create the competition-format:
        with open(
            "tests/files/competition_format_individual_sprint_multiple_finals_1.json",
        ) as file:
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
                status = response.status
                if response.status != HTTPStatus.CREATED:
                    body = await response.json()
                    logger.error(
                        f"Got unexpected status {response.status}, reason {body}."
                    )
                assert status == HTTPStatus.CREATED

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
                if response.status != HTTPStatus.CREATED:
                    logger.error(
                        f"Got unexpected status {response.status} from {http_service}."
                    )
                    body = await response.json()
                    logger.error(f"Got body {body}.")

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
                body = await response.json()
                if response.status != HTTPStatus.OK:
                    body = await response.json()
                    logger.error(
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

        await _print_raceclasses(raceclasses)

        # ACT:

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != HTTPStatus.CREATED:
                body = await response.json()
                logger.error(f"Got unexpected status {response.status}, reason {body}.")
                body = await response.json()
                logger.error(f"Got body {body}.")

        # ASSERT:

        assert response.status == HTTPStatus.CREATED
        assert "/raceplans/" in response.headers[hdrs.LOCATION]

        # We check that raceplan are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("all_1", raceplan)

            with open(
                "tests/files/expected_raceplan_individual_sprint_multiple_finals_1.json",
            ) as file:
                expected_raceplan = json.load(file)

            # And we compare the response to the expected raceplan:
            assert (
                raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
            )
            # Check that all the contestants have been assigned to a Quarterfinal or Round 1:
            assert (
                sum(
                    race["no_of_contestants"]
                    for race in raceplan["races"]
                    if race["round"] in ["Q", "R1"]
                )
                == raceplan["no_of_contestants"]
            )
            assert type(raceplan["races"]) is list
            assert len(raceplan["races"]) == len(expected_raceplan["races"])

            for i, race in enumerate(raceplan["races"]):
                expected_race = expected_raceplan["races"][i]
                assert race["order"] == i + 1
                assert race["order"] == expected_race["order"], (
                    f'"order" in index {i}:{race}\n ne:\n{expected_race}'
                )
                assert (
                    race["raceclass"] == expected_raceplan["races"][i]["raceclass"]
                ), f'"raceclass" in index {i}:{race}\n ne:\n{expected_race}'
                assert (
                    race["start_time"] == expected_raceplan["races"][i]["start_time"]
                ), f'"start_time" in index {i}:{race}\n ne:\n{expected_race}'
                assert (
                    race["no_of_contestants"]
                    == expected_raceplan["races"][i]["no_of_contestants"]
                ), f'"no_of_contestants" in index {i}:{race}\n ne:\n{expected_race}'

        # We also need to check that all the races has raceplan-reference:
        url = f"{http_service}/races?eventId={request_body['event_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            races = await response.json()
            for race in races:
                assert race["raceplan_id"] == raceplan["id"]


@pytest.mark.contract
async def test_generate_raceplan_for_individual_sprint_event_all_2(
    http_service: Any,
    token: MockFixture,
    clear_db: AsyncGenerator,
) -> None:
    """Should return 201 created and a location header with url to the raceplan."""
    # ARRANGE

    event_id = ""
    async with ClientSession() as session:
        # First we need create the competition-format:
        with open(
            "tests/files/competition_format_individual_sprint_multiple_finals_2.json",
        ) as file:
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
                status = response.status
                if response.status != HTTPStatus.CREATED:
                    body = await response.json()
                    logger.error(
                        f"Got unexpected status {response.status}, reason {body}."
                    )
                assert status == HTTPStatus.CREATED

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
                if response.status != HTTPStatus.CREATED:
                    logger.error(
                        f"Got unexpected status {response.status} from {http_service}."
                    )
                    body = await response.json()
                    logger.error(f"Got body {body}.")

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
                body = await response.json()
                if response.status != HTTPStatus.OK:
                    body = await response.json()
                    logger.error(
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

        await _print_raceclasses(raceclasses)

        # ACT:

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != HTTPStatus.CREATED:
                body = await response.json()
                logger.error(f"Got unexpected status {response.status}, reason {body}.")
                body = await response.json()
                logger.error(f"Got body {body}.")

        # ASSERT:

        assert response.status == HTTPStatus.CREATED
        assert "/raceplans/" in response.headers[hdrs.LOCATION]

        # We check that raceplan are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("all_2", raceplan)

            with open(
                "tests/files/expected_raceplan_individual_sprint_multiple_finals_2.json",
            ) as file:
                expected_raceplan = json.load(file)

            # And we compare the response to the expected raceplan:
            assert (
                raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
            )
            # Check that all the contestants have been assigned to a Quarterfinal or Round 1:
            assert (
                sum(
                    race["no_of_contestants"]
                    for race in raceplan["races"]
                    if race["round"] in ["Q", "R1"]
                )
                == raceplan["no_of_contestants"]
            )
            assert type(raceplan["races"]) is list
            assert len(raceplan["races"]) == len(expected_raceplan["races"])

            for i, race in enumerate(raceplan["races"]):
                expected_race = expected_raceplan["races"][i]
                assert race["order"] == i + 1
                assert race["order"] == expected_race["order"], (
                    f'"order" in index {i}:{race}\n ne:\n{expected_race}'
                )
                assert (
                    race["raceclass"] == expected_raceplan["races"][i]["raceclass"]
                ), f'"raceclass" in index {i}:{race}\n ne:\n{expected_race}'
                assert (
                    race["start_time"] == expected_raceplan["races"][i]["start_time"]
                ), f'"start_time" in index {i}:{race}\n ne:\n{expected_race}'
                assert (
                    race["no_of_contestants"]
                    == expected_raceplan["races"][i]["no_of_contestants"]
                ), f'"no_of_contestants" in index {i}:{race}\n ne:\n{expected_race}'

        # We also need to check that all the races has raceplan-reference:
        url = f"{http_service}/races?eventId={request_body['event_id']}"
        async with session.get(url) as response:
            assert response.status == HTTPStatus.OK
            races = await response.json()
            for race in races:
                assert race["raceplan_id"] == raceplan["id"]


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


async def _print_raceclasses(raceclasses: list[dict]) -> None:
    print("group;order;name;ageclasses;no_of_contestants;ranking;distance;event_id")
    raceclasses_sorted = sorted(raceclasses, key=lambda k: (k["group"], k["order"]))

    for raceclass in raceclasses_sorted:
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
    print(f"event_id: {raceplan['event_id']}")
    print(f"no_of_contestants: {raceplan['no_of_contestants']}")
    print("order;start_time;raceclass;round;index;heat;no_of_contestants;rule")
    for race in raceplan["races"]:
        print(
            str(race["order"])
            + ";"
            + str(race["start_time"])
            + ";"
            + str(race["raceclass"])
            + ";"
            + str(race["round"])
            + ";"
            + str(race["index"])
            + ";"
            + str(race["heat"])
            + ";"
            + str(race["no_of_contestants"])
            + ";"
            + str(race["rule"])
        )


async def _dump_raceplan_to_json(raceclass: str, raceplan: dict) -> None:
    with open(
        f"tests/files/tmp_{raceclass}_raceplan_individual_sprint_multiple_finals.json",
        "w",
    ) as file:
        json.dump(raceplan, file)
