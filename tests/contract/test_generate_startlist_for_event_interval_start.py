"""Contract test cases for command generate-startlist-for-event."""
import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, List

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
    async with ClientSession() as session:
        async with session.post(url, headers=headers, json=request_body) as response:
            assert response.status == 200
            body = await response.json()
            if response.status != 200:
                logging.error(
                    f"Got unexpected status {response.status} from {http_service}."
                )
    return body["token"]


@pytest.fixture
@pytest.mark.asyncio
async def clear_db(http_service: Any, token: MockFixture) -> AsyncGenerator:
    """Clear db before and after tests."""
    logging.info(" --- Cleaning db at startup. ---")
    await delete_startlists(http_service, token)
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
    await delete_startlists(http_service, token)
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
            assert response.status == 200
            raceplans = await response.json()
            for raceplan in raceplans:
                raceplan_id = raceplan["id"]
                async with session.delete(
                    f"{url}/{raceplan_id}", headers=headers
                ) as response:
                    assert response.status == 204
                    pass
    logging.info("Clear_db: Deleted all raceplans.")


async def delete_startlists(http_service: Any, token: MockFixture) -> None:
    """Delete all startlists before we start."""
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
                    pass
    logging.info("Clear_db: Deleted all startlists.")


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


@pytest.fixture
async def expected_startlist() -> dict:
    """Create a mock startlist object."""
    with open("tests/files/expected_startlist_interval_start.json", "r") as file:
        startlist = json.load(file)

    return startlist


# Finally we test the test_generate_startlist_for_event function:
@pytest.mark.contract
@pytest.mark.asyncio
async def test_generate_startlist_for_interval_start_entry(
    http_service: Any,
    token: MockFixture,
    clear_db: None,
    expected_startlist: dict,
) -> None:
    """Should return 201 created and a location header with url to startlist."""
    event_id = ""
    async with ClientSession() as session:
        # First we need create the competition-format:
        with open("tests/files/competition_format_interval_start.json", "r") as file:
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
        with open("tests/files/event_interval_start.json", "r") as file:
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
        files = {"file": open("tests/files/all_contestants_eventid_364892.csv", "rb")}
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

        # Then we have to assign bibs to all contestants:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/contestants" in response.headers[hdrs.LOCATION]

        # Get the contestants for debugging purposes:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            _contestants = await response.json()

        await _print_contestants(_contestants)

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
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                body = await response.json()
                logging.error(
                    f"Got unexpected status {response.status}, reason {body}."
                )
            assert response.status == 200
            _raceplans = await response.json()

        await _print_raceplan(_raceplans[0])

        # Finally, we are ready to generate the startlist:
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

        # We check that startlist is actually created:
        startlist_id = response.headers[hdrs.LOCATION].split("/")[-1]
        url = response.headers[hdrs.LOCATION]
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            startlist = await response.json()
            assert "application/json" in response.headers[hdrs.CONTENT_TYPE]
            assert type(startlist) is dict
            assert startlist["id"]
            assert startlist["event_id"] == request_body["event_id"]

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

            i = 0
            for start_entry in startlist["start_entries"]:
                expected_start_entry = expected_startlist["start_entries"][i]
                assert (
                    start_entry["bib"] == expected_start_entry["bib"]
                ), f'"bib" in index {i}:{start_entry}\n ne:\n{expected_start_entry}'
                assert (
                    start_entry["starting_position"]
                    == expected_start_entry["starting_position"]
                ), f'"starting_position" in index {i}:{start_entry}\n ne:\n{expected_start_entry}'
                assert (
                    start_entry["scheduled_start_time"]
                    == expected_start_entry["scheduled_start_time"]
                ), f'"scheduled_start_time" in index {i}:{start_entry}\n ne:\n{expected_start_entry}'
                i += 1

        # We also need to check that all the relevant races has got a list of start_entries:
        url = f'{http_service}/races?eventId={request_body["event_id"]}'
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            races = await response.json()
            no_of_contestants = 0
            for race in races:
                assert (
                    len(race["start_entries"]) > 0
                ), f'race with order {race["order"]} does not have start_entries'
                no_of_contestants += len(race["start_entries"])
            assert no_of_contestants == startlist["no_of_contestants"]

        # We inspect one of the start_entries in the list of races:
        start_entry = races[0]["start_entries"][0]
        assert type(start_entry) is str

        # We inspect the details of the first race, which should include the whole start_entry object:
        url = f'{http_service}/races/{races[0]["id"]}'
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
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
                assert start_entry["scheduled_start_time"]


# ---
async def _decide_group_and_order(raceclass: dict) -> tuple[int, int]:  # noqa: C901
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


async def _print_raceclasses(raceclasses: list[dict]) -> None:
    # print("--- RACECLASSES ---")
    # print("group;order;name;ageclass_name;no_of_contestants;distance;event_id")
    # for raceclass in raceclasses:
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


async def _print_contestants(contestants: List[dict]) -> None:
    # print("--- CONTESTANTS ---")
    # print(f"Number of contestants: {len(contestants)}.")
    # print("bib;ageclass")
    # for contestant in contestants:
    #     print(str(contestant["bib"]) + ";" + str(contestant["ageclass"]))
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
    # with open("tests/files/tmp_startlist.json", "w") as file:
    #     json.dump(startlist, file)
    pass
