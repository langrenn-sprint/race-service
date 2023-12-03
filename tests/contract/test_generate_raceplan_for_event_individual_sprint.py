"""Contract test cases for ping."""
import json
import logging
import os
from typing import Any, AsyncGenerator, List, Tuple

from aiohttp import ClientSession, ContentTypeError, hdrs
import motor.motor_asyncio
import pytest
from pytest_mock import MockFixture

from race_service.utils import db_utils

EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT")
COMPETITION_FORMAT_HOST_SERVER = os.getenv("COMPETITION_FORMAT_HOST_SERVER")
COMPETITION_FORMAT_HOST_PORT = os.getenv("COMPETITION_FORMAT_HOST_PORT")
USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 27017))
DB_NAME = os.getenv("DB_NAME", "races_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


@pytest.fixture(scope="module", autouse=True)
@pytest.mark.asyncio(scope="module")
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


@pytest.fixture(autouse=True)
@pytest.mark.asyncio(scope="module")
async def clear_db() -> AsyncGenerator:
    """Clear db before and after tests."""
    logging.info(" --- Cleaning db at startup. ---")
    mongo = motor.motor_asyncio.AsyncIOMotorClient(  # type: ignore
        host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASSWORD
    )
    try:
        await db_utils.drop_db_and_recreate_indexes(mongo, DB_NAME)
    except Exception as error:
        logging.error(f"Failed to drop database {DB_NAME}: {error}")
        raise error
    logging.info(" --- Testing starts. ---")
    yield
    logging.info(" --- Testing finished. ---")
    logging.info(" --- Cleaning db after testing. ---")
    try:
        await db_utils.drop_db(mongo, DB_NAME)
    except Exception as error:
        logging.error(f"Failed to drop database {DB_NAME}: {error}")
        raise error
    logging.info(" --- Cleaning db done. ---")


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_generate_raceplan_for_individual_sprint_event_J10(
    http_service: Any,
    token: MockFixture,
    clear_db: None,
) -> None:
    """Should return 201 created and a location header with url to the raceplan."""
    # ARRANGE

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
                try:
                    body = await response.json()
                except ContentTypeError:
                    body = None
                    pass

                assert response.status == 201, body if body else ""
                # return the event_id, which is the last item of the path
                event_id = response.headers[hdrs.LOCATION].split("/")[-1]

        # Add list of contestants to event:
        headers = {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        files = {"file": open("tests/files/contestants_J10_17.csv", "rb")}
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

        # Set order on all raceclasses:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses"
        )
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()
            order = 0
            for raceclass in raceclasses:
                id = raceclass["id"]
                order = order + 1
                raceclass["group"] = 1
                raceclass["order"] = order
                raceclass["ranking"] = False
                async with session.put(
                    f"{url}/{id}", headers=headers, json=raceclass
                ) as response:
                    assert response.status == 204

        await _print_raceclasses(raceclasses)

        # ACT

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 201:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
                body = await response.json()
                logging.error(f"Got body {body}.")

        # ASSERT

        assert response.status == 201
        assert "/raceplans/" in response.headers[hdrs.LOCATION]

        # We check that raceplan are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("J10", raceplan)

            with open(
                "tests/files/expected_raceplan_individual_sprint_J10.json", "r"
            ) as file:
                expected_raceplan = json.load(file)

            # And we compare the response to the expected raceplan:
            assert (
                raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
            )
            # Check that all the contestants have been assigned to Round 1:
            assert (
                sum(
                    race["no_of_contestants"]
                    for race in raceplan["races"]
                    if race["round"] == "R1"
                )
                == raceplan["no_of_contestants"]
            )
            # Check that all the contestants have been assigned to round 2:
            assert (
                sum(
                    race["no_of_contestants"]
                    for race in raceplan["races"]
                    if race["round"] == "R2"
                )
                == raceplan["no_of_contestants"]
            )

            assert type(raceplan["races"]) is list
            assert len(raceplan["races"]) == len(expected_raceplan["races"])

            i = 0
            for race in raceplan["races"]:
                expected_race = expected_raceplan["races"][i]
                assert race["raceplan_id"] == raceplan["id"]
                assert race["order"] == i + 1
                assert (
                    race["order"] == expected_race["order"]
                ), f'"order" in index {i}:{race}\n ne:\n{expected_race}'
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
                i += 1


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_generate_raceplan_for_individual_sprint_event_J11(
    http_service: Any,
    token: MockFixture,
    clear_db: None,
) -> None:
    """Should return 201 created and a location header with url to the raceplan."""
    # ARRANGE

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
                if response.status != 201:
                    logging.error(
                        f"Got unexpected status {response.status} from {http_service}."
                    )
                    body = await response.json()
                    logging.error(f"Got body {body}.")
                assert response.status == 201
                # return the event_id, which is the last item of the path
                event_id = response.headers[hdrs.LOCATION].split("/")[-1]

        # Add list of contestants to event:
        headers = {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        files = {"file": open("tests/files/contestants_J11_17.csv", "rb")}
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

        # Set order on all raceclasses:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses"
        )
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()
            order = 0
            for raceclass in raceclasses:
                id = raceclass["id"]
                order = order + 1
                raceclass["group"] = 1
                raceclass["order"] = order
                async with session.put(
                    f"{url}/{id}", headers=headers, json=raceclass
                ) as response:
                    assert response.status == 204

        await _print_raceclasses(raceclasses)

        # ACT

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 201:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
                body = await response.json()
                logging.error(f"Got body {body}.")

        # ASSERT

        assert response.status == 201
        assert "/raceplans/" in response.headers[hdrs.LOCATION]

        # We check that raceplan are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("J11", raceplan)

            with open(
                "tests/files/expected_raceplan_individual_sprint_J11.json", "r"
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

            i = 0
            for race in raceplan["races"]:
                expected_race = expected_raceplan["races"][i]
                assert race["raceplan_id"] == raceplan["id"]
                assert race["order"] == i + 1
                assert (
                    race["order"] == expected_race["order"]
                ), f'"order" in index {i}:{race}\n ne:\n{expected_race}'
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
                i += 1


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_generate_raceplan_for_individual_sprint_event_G11_10(
    http_service: Any,
    token: MockFixture,
    clear_db: None,
) -> None:
    """Should return 201 created and a location header with url to the raceplan."""
    # ARRANGE

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
                if response.status != 201:
                    logging.error(
                        f"Got unexpected status {response.status} from {http_service}."
                    )
                    body = await response.json()
                    logging.error(f"Got body {body}.")
                assert response.status == 201
                # return the event_id, which is the last item of the path
                event_id = response.headers[hdrs.LOCATION].split("/")[-1]

        # Add list of contestants to event:
        headers = {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        files = {"file": open("tests/files/contestants_G11_10.csv", "rb")}
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

        # Set order on all raceclasses:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses"
        )
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()
            order = 0
            for raceclass in raceclasses:
                id = raceclass["id"]
                order = order + 1
                raceclass["group"] = 1
                raceclass["order"] = order
                async with session.put(
                    f"{url}/{id}", headers=headers, json=raceclass
                ) as response:
                    assert response.status == 204

        await _print_raceclasses(raceclasses)

        # ACT

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 201:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
                body = await response.json()
                logging.error(f"Got body {body}.")

        # ASSERT

        assert response.status == 201
        assert "/raceplans/" in response.headers[hdrs.LOCATION]

        # We check that raceplan are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("G11", raceplan)

            with open(
                "tests/files/expected_raceplan_individual_sprint_G11_10.json", "r"
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

            i = 0
            for race in raceplan["races"]:
                expected_race = expected_raceplan["races"][i]
                assert race["raceplan_id"] == raceplan["id"]
                assert race["order"] == i + 1
                assert (
                    race["order"] == expected_race["order"]
                ), f'"order" in index {i}:{race}\n ne:\n{expected_race}'
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
                i += 1


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_generate_raceplan_for_individual_sprint_event_all(
    http_service: Any,
    token: MockFixture,
    clear_db: None,
) -> None:
    """Should return 201 created and a location header with url to the raceplan."""
    # ARRANGE

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
                if response.status != 201:
                    logging.error(
                        f"Got unexpected status {response.status} from {http_service}."
                    )
                    body = await response.json()
                    logging.error(f"Got body {body}.")

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

        await _print_raceclasses(raceclasses)

        # ACT:

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 201:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
                body = await response.json()
                logging.error(f"Got body {body}.")

        # ASSERT:

        assert response.status == 201
        assert "/raceplans/" in response.headers[hdrs.LOCATION]

        # We check that raceplan are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("all", raceplan)

            with open(
                "tests/files/expected_raceplan_individual_sprint.json", "r"
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

            i = 0
            for race in raceplan["races"]:
                expected_race = expected_raceplan["races"][i]
                assert race["order"] == i + 1
                assert (
                    race["order"] == expected_race["order"]
                ), f'"order" in index {i}:{race}\n ne:\n{expected_race}'
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
                i += 1

        # We also need to check that all the races has raceplan-reference:
        url = f'{http_service}/races?eventId={request_body["event_id"]}'
        async with session.get(url) as response:
            assert response.status == 200
            races = await response.json()
            for race in races:
                assert race["raceplan_id"] == raceplan["id"]


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_generate_raceplan_for_individual_sprint_event_G11_7(
    http_service: Any,
    token: MockFixture,
    clear_db: None,
) -> None:
    """Should return 201 created and a location header with url to the raceplan."""
    # ARRANGE

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
                if response.status != 201:
                    logging.error(
                        f"Got unexpected status {response.status} from {http_service}."
                    )
                    body = await response.json()
                    logging.error(f"Got body {body}.")
                assert response.status == 201
                # return the event_id, which is the last item of the path
                event_id = response.headers[hdrs.LOCATION].split("/")[-1]

        # Add list of contestants to event:
        headers = {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        }
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        files = {"file": open("tests/files/contestants_G11_7.csv", "rb")}
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

        # Set order on all raceclasses:
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses"
        )
        async with session.get(url) as response:
            assert response.status == 200
            raceclasses = await response.json()
            order = 0
            for raceclass in raceclasses:
                id = raceclass["id"]
                order = order + 1
                raceclass["group"] = 1
                raceclass["order"] = order
                async with session.put(
                    f"{url}/{id}", headers=headers, json=raceclass
                ) as response:
                    assert response.status == 204

        await _print_raceclasses(raceclasses)

        # ACT

        # Finally, we are ready to generate the raceplan:
        request_body = {"event_id": event_id}
        url = f"{http_service}/raceplans/generate-raceplan-for-event"
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 201:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
                body = await response.json()
                logging.error(f"Got body {body}.")

        # ASSERT

        assert response.status == 201
        assert "/raceplans/" in response.headers[hdrs.LOCATION]

        # We check that raceplan are actually created:
        url = response.headers[hdrs.LOCATION]
        async with session.get(url) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("G11", raceplan)

            with open(
                "tests/files/expected_raceplan_individual_sprint_G11_7.json", "r"
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

            i = 0
            for race in raceplan["races"]:
                expected_race = expected_raceplan["races"][i]
                assert race["raceplan_id"] == raceplan["id"]
                assert race["order"] == i + 1
                assert (
                    race["order"] == expected_race["order"]
                ), f'"order" in index {i}:{race}\n ne:\n{expected_race}'
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
                i += 1


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


async def _print_raceclasses(raceclasses: List[dict]) -> None:
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
    pass


async def _print_raceplan(raceplan: dict) -> None:
    print(f'event_id: {raceplan["event_id"]}')
    print(f'no_of_contestants: {raceplan["no_of_contestants"]}')
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
    pass


async def _dump_raceplan_to_json(raceclass: str, raceplan: dict) -> None:
    with open(
        f"tests/files/tmp_{raceclass}_raceplan_individual_sprint.json", "w"
    ) as file:
        json.dump(raceplan, file)
    pass
