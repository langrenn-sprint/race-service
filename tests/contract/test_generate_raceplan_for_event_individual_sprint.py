"""Contract test cases for ping."""
import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, List, Tuple

from aiohttp import ClientSession, hdrs
import pytest
from pytest_mock import MockFixture

EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT")
USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture
def event_loop(request: Any) -> Any:
    """Redefine the event_loop fixture to have the same scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
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


@pytest.fixture
@pytest.mark.asyncio
async def clear_db(http_service: Any, token: MockFixture) -> AsyncGenerator:
    """Clear db before and after tests."""
    logging.info(" --- Cleaning db at startup. ---")
    await delete_start_entries(http_service, token)
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
    """Delete all raceplans before we start."""
    url = f"{http_service}/raceplans"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            raceplans = await response.json()
            for raceplan in raceplans:
                raceplan_id = raceplan["id"]
                async with session.delete(
                    f"{url}/{raceplan_id}", headers=headers
                ) as response:
                    pass
    logging.info("Clear_db: Deleted all raceplans.")


async def delete_start_entries(http_service: Any, token: MockFixture) -> None:
    """Delete all start_entries before we start."""
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
                        pass
    logging.info("Clear_db: Deleted all start_entries.")


async def delete_races(http_service: Any, token: MockFixture) -> None:
    """Delete all races before we start."""
    url = f"{http_service}/races"
    headers = {
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            races = await response.json()
            for race in races:
                race_id = race["id"]
                async with session.delete(
                    f"{url}/{race_id}", headers=headers
                ) as response:
                    pass
    logging.info("Clear_db: Deleted all races.")


@pytest.mark.contract
@pytest.mark.asyncio
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
            url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats"
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
        async with session.get(url, headers=headers) as response:
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
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("J11", raceplan)

            with open(
                "tests/files/J11_expected_raceplan_individual_sprint.json", "r"
            ) as file:
                expected_raceplan = json.load(file)

            # And we compare the response to the expected raceplan:
            assert (
                raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
            )
            # Check that all the contestants have been assigned to a Quarterfinal:
            assert (
                sum(
                    race["no_of_contestants"]
                    for race in raceplan["races"]
                    if race["round"] == "Q"
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
@pytest.mark.asyncio
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
            url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats"
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
        async with session.get(url, headers=headers) as response:
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
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("G11", raceplan)

            with open(
                "tests/files/G11_expected_raceplan_individual_sprint_10.json", "r"
            ) as file:
                expected_raceplan = json.load(file)

            # And we compare the response to the expected raceplan:
            assert (
                raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
            )
            # Check that all the contestants have been assigned to a Quarterfinal:
            assert (
                sum(
                    race["no_of_contestants"]
                    for race in raceplan["races"]
                    if race["round"] == "Q"
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
@pytest.mark.asyncio
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
            url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats"
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
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("all", raceplan)

            with open(
                "tests/files/all_expected_raceplan_individual_sprint.json", "r"
            ) as file:
                expected_raceplan = json.load(file)

            # And we compare the response to the expected raceplan:
            assert (
                raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
            )
            # Check that all the contestants have been assigned to a Quarterfinal:
            assert (
                sum(
                    race["no_of_contestants"]
                    for race in raceplan["races"]
                    if race["round"] == "Q"
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
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            races = await response.json()
            for race in races:
                assert race["raceplan_id"] == raceplan["id"]


@pytest.mark.contract
@pytest.mark.asyncio
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
            url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/competition-formats"
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
        async with session.get(url, headers=headers) as response:
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
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            raceplan = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(raceplan) is dict
            assert raceplan["id"]
            assert raceplan["event_id"] == request_body["event_id"]

            await _print_raceplan(raceplan)
            await _dump_raceplan_to_json("G11", raceplan)

            with open(
                "tests/files/G11_expected_raceplan_individual_sprint_7.json", "r"
            ) as file:
                expected_raceplan = json.load(file)

            # And we compare the response to the expected raceplan:
            assert (
                raceplan["no_of_contestants"] == expected_raceplan["no_of_contestants"]
            )
            # Check that all the contestants have been assigned to a Quarterfinal:
            assert (
                sum(
                    race["no_of_contestants"]
                    for race in raceplan["races"]
                    if race["round"] == "Q"
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


async def _print_raceclasses(raceclasses: List[dict]) -> None:
    # print("group;order;name;ageclass_name;no_of_contestants;distance;event_id")
    # raceclasses_sorted = sorted(raceclasses, key=lambda k: (k["group"], k["order"]))

    # for raceclass in raceclasses_sorted:
    #     print(
    #         str(raceclass["group"])
    #         + ";"
    #         + str(raceclass["order"])
    #         + ";"
    #         + raceclass["name"]
    #         + ";"
    #         + raceclass["ageclass_name"]
    #         + ";"
    #         + str(raceclass["no_of_contestants"])
    #         + ";"
    #         + str(raceclass["distance"])
    #         + ";"
    #         + raceclass["event_id"]
    #     )
    pass


async def _print_raceplan(raceplan: dict) -> None:
    # print(f'event_id: {raceplan["event_id"]}')
    # print(f'no_of_contestants: {raceplan["no_of_contestants"]}')
    # print("order;start_time;raceclass;round;index;heat;no_of_contestants;rule")
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
    #         + ";"
    #         + str(race["rule"])
    #     )
    pass


async def _dump_raceplan_to_json(raceclass: str, raceplan: dict) -> None:
    # with open(f"tests/files/tmp_{raceclass}_raceplan.json", "w") as file:
    #     json.dump(raceplan, file)
    pass
