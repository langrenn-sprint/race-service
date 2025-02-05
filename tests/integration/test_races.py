"""Integration test cases for the races route."""

import os
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from json import dumps
from typing import Any

import jwt
import pytest
from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
from pytest_mock import MockFixture

from race_service.adapters import (
    NotSupportedRaceDatatypeError,
    RaceNotFoundError,
)
from race_service.models import (
    IndividualSprintRace,
    IntervalStartRace,
    RaceResult,
    StartEntry,
    TimeEvent,
)

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "user", "roles": ["user"]}
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
async def new_race_interval_start() -> IntervalStartRace:
    """Create a race object."""
    return IntervalStartRace(
        id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
        results={"Finish": "race_result_1"},
        datatype="interval_start",
    )


@pytest.fixture
async def race_interval_start() -> IntervalStartRace:
    """Create a mock race object."""
    return IntervalStartRace(
        id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
        results={"Finish": "race_result_1"},
        datatype="interval_start",
    )


@pytest.fixture
async def new_race_individual_sprint() -> IndividualSprintRace:
    """Create a mock race object."""
    return IndividualSprintRace(
        id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
        results={"Finish": "race_result_1"},
        round="Q",
        index="",
        heat=1,
        rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
        datatype="individual_sprint",
    )


@pytest.fixture
async def race_individual_sprint() -> IndividualSprintRace:
    """Create a mock race object."""
    return IndividualSprintRace(
        id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
        results={"Finish": "race_result_1"},
        round="Q",
        index="",
        heat=1,
        rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
        datatype="individual_sprint",
    )


START_ENTRIES: list[StartEntry] = [
    StartEntry(
        id="11",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=1,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        starting_position=1,
        startlist_id="1",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="22",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=2,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:00:30"),
        starting_position=2,
        startlist_id="1",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="33",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=3,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:01:00"),
        starting_position=1,
        startlist_id="1",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="44",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=4,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:01:30"),
        starting_position=2,
        startlist_id="1",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="55",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=5,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:02:00"),
        starting_position=1,
        startlist_id="1",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="66",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=6,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:02:30"),
        starting_position=2,
        startlist_id="1",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="77",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=7,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:03:00"),
        starting_position=1,
        startlist_id="1",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="88",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=8,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:03:30"),
        starting_position=2,
        startlist_id="1",
        status=None,
        changelog=None,
    ),
]


TIME_EVENTS: list[TimeEvent] = [
    TimeEvent(
        id="time_event_1",
        bib=8,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:33:30"),
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        rank=1,
        status="OK",
        changelog=None,
        race=None,
        next_race=None,
        next_race_id=None,
        next_race_position=None,
    ),
    TimeEvent(
        id="time_event_2",
        bib=7,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:34:30"),
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        rank=2,
        status="OK",
        changelog=None,
        race=None,
        next_race=None,
        next_race_id=None,
        next_race_position=None,
    ),
]


@pytest.fixture
async def mock_race_result() -> RaceResult:
    """Create a mock race-result object."""
    return RaceResult(
        id="race_result_1",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        timing_point="Finish",
        no_of_contestants=2,
        ranking_sequence=["time_event_1", "time_event_2"],
        status=0,
    )


@pytest.fixture
async def start_entries_() -> list[StartEntry]:
    """Create a mock start-entry object."""
    return START_ENTRIES


def get_start_entry_by_id(db: Any, id_: str) -> StartEntry:
    """Mock function to look up correct start-entry from list."""
    return next(start_entry for start_entry in START_ENTRIES if start_entry.id == id_)


def get_time_event_by_id(db: Any, id_: str) -> TimeEvent:
    """Mock function to look up correct time-event from list."""
    return next(time_event for time_event in TIME_EVENTS if time_event.id == id_)


@pytest.fixture
async def new_race_unsupported_datatype() -> dict:
    """Create a race object."""
    return {
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 8,
        "max_no_of_contestants": 10,
        "datatype": "unsupported",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_race_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_race_interval_start: IntervalStartRace,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 405 Method Not Allowed."""
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.services.races_service.create_id",
        return_value=race_id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=race_id,
    )

    request_body = dumps(
        new_race_interval_start.to_dict(), indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/races", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_by_id_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    mock_race_result: RaceResult,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return OK, and a body containing one race."""
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/races/{race_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == race_id
        assert body["event_id"] == race_interval_start.event_id
        assert body["raceclass"] == race_interval_start.raceclass
        assert body["order"] == race_interval_start.order
        assert body["start_time"] == race_interval_start.start_time.isoformat()
        assert body["no_of_contestants"] == race_interval_start.no_of_contestants
        assert body["event_id"] == race_interval_start.event_id
        assert body["datatype"] == race_interval_start.datatype
        for start_entry in body["start_entries"]:
            assert type(start_entry) is dict
            assert (
                start_entry
                == get_start_entry_by_id(db=None, id_=start_entry["id"]).to_dict()
            )
        assert type(body["results"]) is dict
        for key in body["results"]:
            assert type(key) is str
            race_result = body["results"][key]
            assert type(race_result) is dict  # value of dict should be a RaceResult
            assert race_result["id"] == mock_race_result.id
            assert race_result["race_id"] == mock_race_result.race_id
            assert (
                race_result["no_of_contestants"] == mock_race_result.no_of_contestants
            )
            assert type(race_result["ranking_sequence"])
            assert len(race_result["ranking_sequence"]) == len(
                mock_race_result.ranking_sequence
            )
            # Simple test to check if the ranking_sequence is sorted:
            assert (
                race_result["ranking_sequence"][0]["rank"]
                < race_result["ranking_sequence"][1]["rank"]
            ), "ranking_sequence is not sorted correctly."
            for time_event in race_result["ranking_sequence"]:
                assert type(time_event) is dict
                expected_time_event = get_time_event_by_id(
                    db=None, id_=time_event["id"]
                )
                assert time_event == expected_time_event.to_dict()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_by_id_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    mock_race_result: RaceResult,
    race_individual_sprint: IndividualSprintRace,
) -> None:
    """Should return OK, and a body containing one race."""
    race_id = race_individual_sprint.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/races/{race_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == race_id
        assert body["event_id"] == race_individual_sprint.event_id
        assert body["raceclass"] == race_individual_sprint.raceclass
        assert body["order"] == race_individual_sprint.order
        assert body["start_time"] == race_individual_sprint.start_time.isoformat()
        assert body["no_of_contestants"] == race_individual_sprint.no_of_contestants
        assert body["event_id"] == race_individual_sprint.event_id
        assert body["round"] == race_individual_sprint.round
        assert body["index"] == race_individual_sprint.index
        assert body["heat"] == race_individual_sprint.heat
        assert body["rule"] == race_individual_sprint.rule
        assert body["datatype"] == race_individual_sprint.datatype
        for start_entry in body["start_entries"]:
            assert type(start_entry) is dict
            assert (
                start_entry
                == get_start_entry_by_id(db=None, id_=start_entry["id"]).to_dict()
            )
        assert type(body["results"]) is dict
        for key in body["results"]:
            assert type(key) is str
            race_result = body["results"][key]
            assert type(race_result) is dict  # value of dict should be a RaceResult
            assert race_result["id"] == mock_race_result.id
            assert race_result["race_id"] == mock_race_result.race_id
            assert (
                race_result["no_of_contestants"] == mock_race_result.no_of_contestants
            )
            assert type(race_result["ranking_sequence"])
            assert len(race_result["ranking_sequence"]) > 0
            for time_event in race_result["ranking_sequence"]:
                assert type(time_event) is dict
                expected_time_event = get_time_event_by_id(
                    db=None, id_=time_event["id"]
                )
                assert time_event == expected_time_event.to_dict()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_races_by_event_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return OK, and a body containing one race."""
    event_id = race_interval_start.event_id
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=[race_interval_start],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/races?eventId={event_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == race_id
        assert body[0]["event_id"] == race_interval_start.event_id
        assert body[0]["raceclass"] == race_interval_start.raceclass
        assert body[0]["order"] == race_interval_start.order
        assert body[0]["start_time"] == race_interval_start.start_time.isoformat()
        assert body[0]["no_of_contestants"] == race_interval_start.no_of_contestants
        assert body[0]["event_id"] == race_interval_start.event_id
        assert body[0]["start_entries"] == race_interval_start.start_entries
        assert body[0]["datatype"] == race_interval_start.datatype


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_races_by_event_id_and_raceclass(
    client: _TestClient,
    mocker: MockFixture,
    mock_race_result: RaceResult,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return OK, and a body containing one race."""
    event_id = race_interval_start.event_id
    raceclass = race_interval_start.raceclass
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id_and_raceclass",
        return_value=[race_interval_start],
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/races?eventId={event_id}&raceclass={raceclass}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == race_id
        assert body[0]["event_id"] == race_interval_start.event_id
        assert body[0]["raceclass"] == raceclass
        assert body[0]["order"] == race_interval_start.order
        assert body[0]["start_time"] == race_interval_start.start_time.isoformat()
        assert body[0]["no_of_contestants"] == race_interval_start.no_of_contestants
        assert body[0]["event_id"] == race_interval_start.event_id
        assert len(body[0]["start_entries"]) == len(race_interval_start.start_entries)
        assert body[0]["datatype"] == race_interval_start.datatype
        assert body[0]["id"] == mock_race_result.race_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_races_by_event_id_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_individual_sprint: IndividualSprintRace,
) -> None:
    """Should return OK, and a body containing one race."""
    event_id = race_individual_sprint.event_id
    race_id = race_individual_sprint.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=[race_individual_sprint],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/races?eventId={event_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == race_id
        assert body[0]["raceclass"] == race_individual_sprint.raceclass
        assert body[0]["order"] == race_individual_sprint.order
        assert body[0]["start_time"] == race_individual_sprint.start_time.isoformat()
        assert body[0]["no_of_contestants"] == race_individual_sprint.no_of_contestants
        assert body[0]["event_id"] == race_individual_sprint.event_id
        assert body[0]["start_entries"] == race_individual_sprint.start_entries
        assert body[0]["round"] == race_individual_sprint.round
        assert body[0]["index"] == race_individual_sprint.index
        assert body[0]["heat"] == race_individual_sprint.heat
        assert body[0]["rule"] == race_individual_sprint.rule
        assert body[0]["datatype"] == race_individual_sprint.datatype


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_races_by_event_id_and_raceclass_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    mock_race_result: RaceResult,
    token: MockFixture,
    race_individual_sprint: IndividualSprintRace,
) -> None:
    """Should return OK, and a body containing one race."""
    event_id = race_individual_sprint.event_id
    race_id = race_individual_sprint.id
    raceclass = race_individual_sprint.raceclass
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id_and_raceclass",
        return_value=[race_individual_sprint],
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/races?eventId={event_id}&raceclass={raceclass}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == race_id
        assert body[0]["raceclass"] == raceclass
        assert body[0]["order"] == race_individual_sprint.order
        assert body[0]["start_time"] == race_individual_sprint.start_time.isoformat()
        assert body[0]["no_of_contestants"] == race_individual_sprint.no_of_contestants
        assert body[0]["event_id"] == race_individual_sprint.event_id
        assert body[0]["round"] == race_individual_sprint.round
        assert body[0]["index"] == race_individual_sprint.index
        assert body[0]["heat"] == race_individual_sprint.heat
        assert body[0]["rule"] == race_individual_sprint.rule
        assert body[0]["datatype"] == race_individual_sprint.datatype
        assert body[0]["id"] == mock_race_result.race_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return No Content."""
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(
        race_interval_start.to_dict(), indent=4, sort_keys=True, default=str
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(f"/races/{race_id}", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_individual_sprint: IndividualSprintRace,
) -> None:
    """Should return No Content."""
    race_id = race_individual_sprint.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(
        race_individual_sprint.to_dict(), indent=4, sort_keys=True, default=str
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(f"/races/{race_id}", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_races(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return OK and a valid json body."""
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_all_races",
        return_value=[race_interval_start],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.get("/races")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        races = await resp.json()
        assert type(races) is list
        assert len(races) > 0
        assert races[0]["id"] == race_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_races_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_individual_sprint: IndividualSprintRace,
) -> None:
    """Should return OK and a valid json body."""
    race_id = race_individual_sprint.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_all_races",
        return_value=[race_individual_sprint],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.get("/races")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) > 0
        assert body[0]["id"] == race_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return No Content."""
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=race_id,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.delete(f"/races/{race_id}", headers=headers)
        assert resp.status == HTTPStatus.NO_CONTENT


# Bad cases


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": race_id}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(f"/races/{race_id}", headers=headers, json=request_body)
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_different_id_in_body(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    update_body = deepcopy(race_interval_start)
    update_body.id = "different_id"
    request_body = dumps(update_body.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(f"/races/{race_id}", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_by_id_unsupported_datatype(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    mock_race_result: RaceResult,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return OK, and a body containing one race."""
    race_id = race_interval_start.id
    race_unsupported_datatype = deepcopy(race_interval_start)
    race_unsupported_datatype.datatype = "unsupported_datatype"
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=NotSupportedRaceDatatypeError(
            f"Datatype {race_unsupported_datatype.datatype} not supported."
        ),
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/races/{race_id}")
        assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race_interval_start: IntervalStartRace
) -> None:
    """Should return 401 Unauthorized."""
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    request_body = dumps(race_interval_start, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.put(f"/races/{race_id}", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race_interval_start: IntervalStartRace
) -> None:
    """Should return 401 Unauthorized."""
    race_id = race_interval_start.id
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(
            f"Race with id {race_interval_start.id} not found."
        ),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=race_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.delete(f"/races/{race_id}")
        assert resp.status == HTTPStatus.UNAUTHORIZED


# Forbidden:
@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_unauthorized(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 404 Not found."""
    race_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
    }

    request_body = dumps(race_interval_start, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=403)
        resp = await client.put(f"/races/{race_id}", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.FORBIDDEN


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    race_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError("Race with id {race.id} not found."),
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/races/{race_id}")
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 404 Not found."""
    race_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(
            f"Race with id {race_interval_start.id} not found."
        ),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(
        race_interval_start.to_dict(), indent=4, sort_keys=True, default=str
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.put(f"/races/{race_id}", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_unknown_datatype(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 422 Unprocessable entity."""
    race_unknown_datatype = deepcopy(race_interval_start)
    race_unknown_datatype.datatype = "unknown"
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(
            f"Race with id {race_interval_start.id} not found."
        ),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(
        race_unknown_datatype.to_dict(), indent=4, sort_keys=True, default=str
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.put(
            f"/races/{race_unknown_datatype.id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    race_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError("Race with id {race.id} not found."),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=None,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.delete(f"/races/{race_id}", headers=headers)
        assert resp.status == HTTPStatus.NOT_FOUND
