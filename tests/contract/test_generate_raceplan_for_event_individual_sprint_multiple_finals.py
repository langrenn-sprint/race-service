"""Contract test cases for ping."""

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
    async with AsyncClient() as client:
        # First we need create the competition-format:
        with open(
            "tests/files/competition_format_individual_sprint_multiple_finals_1.json",
        ) as file:
            competition_format = json.load(file)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"
            request_body = competition_format
            response = await client.post(url, headers=headers, json=request_body)
            status = response.status_code
            if response.status_code != HTTPStatus.CREATED:
                body = response.json()
                logger.error(
                    f"Got unexpected status {response.status_code}, reason {body}."
                )
            assert status == HTTPStatus.CREATED

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
            if response.status_code != HTTPStatus.CREATED:
                logger.error(
                    f"Got unexpected status {response.status_code} from {http_service}."
                )
                body = response.json()
                logger.error(f"Got body {body}.")

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

        await _print_raceclasses(raceclasses)

        # ACT:

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        response = await client.post(url, headers=headers, json=request_body)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
            logger.error(
                f"Got unexpected status {response.status_code}, reason {body}."
            )
            body = response.json()
            logger.error(f"Got body {body}.")

        # ASSERT:

        assert response.status_code == HTTPStatus.CREATED
        assert "/raceplans/" in response.headers["Location"]

        # We check that raceplan are actually created:
        url = response.headers["Location"]
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan = response.json()
        assert "application/json" in response.headers["Content-Type"]
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
        assert raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
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
            assert race["raceclass"] == expected_raceplan["races"][i]["raceclass"], (
                f'"raceclass" in index {i}:{race}\n ne:\n{expected_race}'
            )
            assert race["start_time"] == expected_raceplan["races"][i]["start_time"], (
                f'"start_time" in index {i}:{race}\n ne:\n{expected_race}'
            )
            assert (
                race["no_of_contestants"]
                == expected_raceplan["races"][i]["no_of_contestants"]
            ), f'"no_of_contestants" in index {i}:{race}\n ne:\n{expected_race}'

        # We also need to check that all the races has raceplan-reference:
        url = f"{http_service}/races?eventId={request_body['event_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        races = response.json()
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
    async with AsyncClient() as client:
        # First we need create the competition-format:
        with open(
            "tests/files/competition_format_individual_sprint_multiple_finals_2.json",
        ) as file:
            competition_format = json.load(file)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            url = f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}/competition-formats"
            request_body = competition_format
            response = await client.post(url, headers=headers, json=request_body)
            status = response.status_code
            if response.status_code != HTTPStatus.CREATED:
                body = response.json()
                logger.error(
                    f"Got unexpected status {response.status_code}, reason {body}."
                )
            assert status == HTTPStatus.CREATED

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
            if response.status_code != HTTPStatus.CREATED:
                logger.error(
                    f"Got unexpected status {response.status_code} from {http_service}."
                )
                body = response.json()
                logger.error(f"Got body {body}.")

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

        await _print_raceclasses(raceclasses)

        # ACT:

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        response = await client.post(url, headers=headers, json=request_body)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
            logger.error(
                f"Got unexpected status {response.status_code}, reason {body}."
            )
            body = response.json()
            logger.error(f"Got body {body}.")

        # ASSERT:

        assert response.status_code == HTTPStatus.CREATED
        assert "/raceplans/" in response.headers["Location"]

        # We check that raceplan are actually created:
        url = response.headers["Location"]
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan = response.json()
        assert "application/json" in response.headers["Content-Type"]
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
        assert raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
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
            assert race["raceclass"] == expected_raceplan["races"][i]["raceclass"], (
                f'"raceclass" in index {i}:{race}\n ne:\n{expected_race}'
            )
            assert race["start_time"] == expected_raceplan["races"][i]["start_time"], (
                f'"start_time" in index {i}:{race}\n ne:\n{expected_race}'
            )
            assert (
                race["no_of_contestants"]
                == expected_raceplan["races"][i]["no_of_contestants"]
            ), f'"no_of_contestants" in index {i}:{race}\n ne:\n{expected_race}'

        # We also need to check that all the races has raceplan-reference:
        url = f"{http_service}/races?eventId={request_body['event_id']}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        races = response.json()
        for race in races:
            assert race["raceplan_id"] == raceplan["id"]


# ---


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
        json.dump(raceplan, file, ensure_ascii=False)
