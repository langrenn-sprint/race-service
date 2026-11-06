"""Contract test cases for ping."""

import json
import logging
import os
from collections.abc import AsyncGenerator
from http import HTTPStatus
from typing import Any
from urllib.parse import urlsplit

import pytest
from httpx import AsyncClient
from pymongo import AsyncMongoClient
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
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=request_body)
        assert response.status_code == HTTPStatus.OK
        body = response.json()
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
async def expected_raceplan() -> dict:
    """Create a mock raceplan object."""
    with open("tests/files/expected_raceplan_interval_start.json") as file:
        return json.load(file)


# Finally we test the test_generate_raceplan_for_event function:
@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_generate_raceplan_for_interval_start_entry(
    http_service: Any,
    token: MockFixture,
    clear_db: None,
    expected_raceplan: dict,
    competition_format_url: str,
    events_url: str,
) -> None:
    """Should return 201 created and a location header with url to raceplan."""
    event_id = ""
    async with AsyncClient() as client:
        # First we need create the competition-format:
        with open("tests/files/competition_format_interval_start.json") as file:
            competition_format = json.load(file)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            url = f"{competition_format_url}/competition-formats"
            request_body = competition_format
            response = await client.post(url, headers=headers, json=request_body)
            assert response.status_code == HTTPStatus.CREATED

        # Next we create the event:
        with open("tests/files/event_interval_start.json") as file:
            event = json.load(file)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            url = f"{events_url}/events"
            request_body = event
            response = await client.post(url, headers=headers, json=request_body)
            try:
                body = response.json()
            except json.JSONDecodeError:
                body = None

            assert response.status_code == HTTPStatus.CREATED, body or ""
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
        await _print_raceclasses(raceclasses)

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        response = await client.post(url, headers=headers, json=request_body)
        if response.status_code != HTTPStatus.CREATED:
            body = response.json()
            logger.error(
                f"Got unexpected status {response.status_code}, reason {body}."
            )
        assert response.status_code == HTTPStatus.CREATED
        assert "/raceplans/" in response.headers["Location"]

        # We check that raceplan are actually created:
        # Location uses the service's configured host, not Docker's port
        url = f"{http_service}{urlsplit(response.headers['Location']).path}"
        response = await client.get(url)
        assert response.status_code == HTTPStatus.OK
        raceplan = response.json()
        assert "application/json" in response.headers["Content-Type"]
        assert type(raceplan) is dict
        assert raceplan["id"]
        assert raceplan["event_id"] == request_body["event_id"]

        await _print_raceplan(raceplan)
        await _dump_raceplan_to_json("all", raceplan)

        # And we compare the response to the expected raceplan:
        assert raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
        assert len(raceplan["races"]) == len(expected_raceplan["races"])

        for i, race in enumerate(raceplan["races"]):
            expected_race = expected_raceplan["races"][i]
            assert race["raceplan_id"] == raceplan["id"]
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
    # print("--- raceclassES ---")
    # print("group;order;name;ageclasses;no_of_contestants;distance;event_id")
    # for raceclass in raceclasses:
    #     print(
    #         str(raceclass["group"])
    #         + ";"
    #         + str(raceclass["order"])
    #         + ";"
    #         + raceclass["name"]
    #         + ";"
    #         + "".join(raceclass["ageclasses"])
    #         + ";"
    #         + str(raceclass["no_of_contestants"])
    #         + ";"
    #         + str(raceclass["distance"])
    #         + ";"
    #         + raceclass["event_id"]
    #     )
    pass


async def _print_raceplan(raceplan: dict) -> None:
    # print("--- RACEPLAN ---")
    # print(f'event_id: {raceplan["event_id"]}')
    # print(f'no_of_contestants: {raceplan["no_of_contestants"]}')
    # print("order;start_time;raceclass;no_of_contestants")
    # for race in raceplan["races"]:
    #     print(
    #         str(race["order"])
    #         + ";"
    #         + str(race["start_time"])
    #         + ";"
    #         + str(race["raceclass"])
    #         + ";"
    #         + str(race["no_of_contestants"])
    #     )
    pass


async def _dump_raceplan_to_json(raceclass: str, raceplan: dict) -> None:
    with open(f"tests/files/tmp_{raceclass}_raceplan_interval_start.json", "w") as file:
        json.dump(raceplan, file, ensure_ascii=False)
