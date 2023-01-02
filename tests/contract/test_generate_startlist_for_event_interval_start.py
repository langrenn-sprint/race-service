"""Contract test cases for command generate-startlist-for-event."""
import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, List, Tuple

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


@pytest.fixture(autouse=True)
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


@pytest.fixture(scope="module")
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

        # Then we have to assign bibs to all contestants:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants/assign-bibs"
        async with session.post(url, headers=headers) as response:
            assert response.status == 201
            assert f"/events/{event_id}/contestants" in response.headers[hdrs.LOCATION]

        # Get the contestants for debugging purposes:
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"
        async with session.get(url) as response:
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
        async with session.get(url) as response:
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
        async with session.get(url) as response:
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
        async with session.get(url) as response:
            assert response.status == 200
            races = await response.json()
            no_of_contestants = 0
            for race in races:
                assert (
                    len(race["start_entries"]) > 0
                ), f'race with order {race["order"]} does not have start_entries'
                no_of_contestants += len(race["start_entries"])

                # We also check that the start_entries are sorted by starting_position:
                url = f'{http_service}/races/{race["id"]}/start-entries'
                async with session.get(url) as response:
                    assert response.status == 200
                    start_entries = await response.json()
                _starting_position: List[int] = [
                    start_entry["starting_position"] for start_entry in start_entries
                ]
                assert all(
                    _starting_position[i] <= _starting_position[i + 1]
                    for i in range(len(_starting_position) - 1)
                )
            assert no_of_contestants == startlist["no_of_contestants"]

        # We inspect one of the start_entries in the list of races:
        start_entry = races[0]["start_entries"][0]
        assert type(start_entry) is str

        # We inspect the details of the first race, which should include the whole start_entry object:
        url = f'{http_service}/races/{races[0]["id"]}'
        async with session.get(url) as response:
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
    # print("--- RACECLASSES ---")
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
    # with open("tests/files/tmp_startlist_interval_start.json", "w") as file:
    #     json.dump(startlist, file)
    pass
