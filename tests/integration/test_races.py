"""Integration test cases for the races route."""

import os
import uuid
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from json import dumps

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app.adapters import (
    NotSupportedRaceDatatypeError,
    RaceNotFoundError,
)
from app.models import (
    IndividualSprintRace,
    IntervalStartRace,
    RaceResult,
    StartEntry,
    TimeEvent,
)


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {
        "username": os.getenv("ADMIN_USERNAME"),
        "exp": 9999999999,
        "role": "admin",
    }
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"username": "user", "exp": 9999999999, "role": "user"}
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
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
        results={"Finish": "50b75bea-866a-50fc-bde0-78cc68b04fec"},
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
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
        results={"Finish": "50b75bea-866a-50fc-bde0-78cc68b04fec"},
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
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
        results={"Finish": "50b75bea-866a-50fc-bde0-78cc68b04fec"},
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
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
        results={"Finish": "50b75bea-866a-50fc-bde0-78cc68b04fec"},
        round="Q",
        index="",
        heat=1,
        rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
        datatype="individual_sprint",
    )


START_ENTRIES: list[StartEntry] = [
    StartEntry(
        id="f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=1,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        starting_position=1,
        startlist_id="311ad0e6-2c39-506d-b2f9-1c317c38b50b",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="5152cfad-4307-565b-8e66-e81f02d8d4e3",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=2,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:00:30"),
        starting_position=2,
        startlist_id="311ad0e6-2c39-506d-b2f9-1c317c38b50b",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=3,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:01:00"),
        starting_position=1,
        startlist_id="311ad0e6-2c39-506d-b2f9-1c317c38b50b",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=4,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:01:30"),
        starting_position=2,
        startlist_id="311ad0e6-2c39-506d-b2f9-1c317c38b50b",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="91547337-a276-5407-962e-a591c95b0478",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=5,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:02:00"),
        starting_position=1,
        startlist_id="311ad0e6-2c39-506d-b2f9-1c317c38b50b",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="35106e04-9f97-5e62-a112-fbfd7cc6924b",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=6,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:02:30"),
        starting_position=2,
        startlist_id="311ad0e6-2c39-506d-b2f9-1c317c38b50b",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=7,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:03:00"),
        starting_position=1,
        startlist_id="311ad0e6-2c39-506d-b2f9-1c317c38b50b",
        status=None,
        changelog=None,
    ),
    StartEntry(
        id="6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=8,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:03:30"),
        starting_position=2,
        startlist_id="311ad0e6-2c39-506d-b2f9-1c317c38b50b",
        status=None,
        changelog=None,
    ),
]


TIME_EVENTS: list[TimeEvent] = [
    TimeEvent(
        id="1ba641c0-ed88-5934-9b13-667d34430228",
        bib=8,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
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
        id="5c369f7a-1967-5a65-91da-2f6f99e3e86d",
        bib=7,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
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
        id="50b75bea-866a-50fc-bde0-78cc68b04fec",
        race_id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        timing_point="Finish",
        no_of_contestants=2,
        ranking_sequence=[
            "1ba641c0-ed88-5934-9b13-667d34430228",
            "5c369f7a-1967-5a65-91da-2f6f99e3e86d",
        ],
        status=0,
    )


@pytest.fixture
async def start_entries_() -> list[StartEntry]:
    """Create a mock start-entry object."""
    return START_ENTRIES


def get_start_entry_by_id(id_: str) -> StartEntry:
    """Mock function to look up correct start-entry from list."""
    return next(
        start_entry for start_entry in START_ENTRIES if str(start_entry.id) == str(id_)
    )


def get_time_event_by_id(id_: str) -> TimeEvent:
    """Mock function to look up correct time-event from list."""
    return next(
        time_event for time_event in TIME_EVENTS if str(time_event.id) == str(id_)
    )


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
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_race_interval_start: IntervalStartRace,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 405 Method Not Allowed."""
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.create_race",
        return_value=race_id,
    )

    request_body = dumps(
        new_race_interval_start.model_dump(mode="json"),
        indent=4,
        sort_keys=True,
        default=str,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/races", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_by_id_interval_start(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    mock_race_result: RaceResult,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return OK, and a body containing one race."""
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    resp = client.get(f"/races/{race_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(race_id)
    assert body["event_id"] == str(race_interval_start.event_id)
    assert body["raceclass"] == race_interval_start.raceclass
    assert body["order"] == race_interval_start.order
    assert body["start_time"] == race_interval_start.start_time.isoformat()
    assert body["no_of_contestants"] == race_interval_start.no_of_contestants
    assert body["event_id"] == str(race_interval_start.event_id)
    assert body["datatype"] == race_interval_start.datatype
    for start_entry in body["start_entries"]:
        assert type(start_entry) is dict
        assert start_entry == get_start_entry_by_id(id_=start_entry["id"]).model_dump(
            mode="json"
        )
    assert type(body["results"]) is dict
    for key in body["results"]:
        assert type(key) is str
        race_result = body["results"][key]
        assert type(race_result) is dict  # value of dict should be a RaceResult
        assert race_result["id"] == str(mock_race_result.id)
        assert race_result["race_id"] == str(mock_race_result.race_id)
        assert race_result["no_of_contestants"] == mock_race_result.no_of_contestants
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
            expected_time_event = get_time_event_by_id(id_=time_event["id"])
            assert time_event == expected_time_event.model_dump(mode="json")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_by_id_individual_sprint(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    mock_race_result: RaceResult,
    race_individual_sprint: IndividualSprintRace,
) -> None:
    """Should return OK, and a body containing one race."""
    race_id = race_individual_sprint.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_individual_sprint,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    resp = client.get(f"/races/{race_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(race_id)
    assert body["event_id"] == str(race_individual_sprint.event_id)
    assert body["raceclass"] == race_individual_sprint.raceclass
    assert body["order"] == race_individual_sprint.order
    assert body["start_time"] == race_individual_sprint.start_time.isoformat()
    assert body["no_of_contestants"] == race_individual_sprint.no_of_contestants
    assert body["event_id"] == str(race_individual_sprint.event_id)
    assert body["round"] == race_individual_sprint.round
    assert body["index"] == race_individual_sprint.index
    assert body["heat"] == race_individual_sprint.heat
    assert body["rule"] == race_individual_sprint.rule
    assert body["datatype"] == race_individual_sprint.datatype
    for start_entry in body["start_entries"]:
        assert type(start_entry) is dict
        assert start_entry == get_start_entry_by_id(id_=start_entry["id"]).model_dump(
            mode="json"
        )
    assert type(body["results"]) is dict
    for key in body["results"]:
        assert type(key) is str
        race_result = body["results"][key]
        assert type(race_result) is dict  # value of dict should be a RaceResult
        assert race_result["id"] == str(mock_race_result.id)
        assert race_result["race_id"] == str(mock_race_result.race_id)
        assert race_result["no_of_contestants"] == mock_race_result.no_of_contestants
        assert type(race_result["ranking_sequence"])
        assert len(race_result["ranking_sequence"]) > 0
        for time_event in race_result["ranking_sequence"]:
            assert type(time_event) is dict
            expected_time_event = get_time_event_by_id(id_=time_event["id"])
            assert time_event == expected_time_event.model_dump(mode="json")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_races_by_event_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return OK, and a body containing one race."""
    event_id = race_interval_start.event_id
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=[race_interval_start],
    )

    resp = client.get(f"/races?eventId={event_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["id"] == str(race_id)
    assert body[0]["event_id"] == str(race_interval_start.event_id)
    assert body[0]["raceclass"] == race_interval_start.raceclass
    assert body[0]["order"] == race_interval_start.order
    assert body[0]["start_time"] == race_interval_start.start_time.isoformat()
    assert body[0]["no_of_contestants"] == race_interval_start.no_of_contestants
    assert body[0]["event_id"] == str(race_interval_start.event_id)
    assert body[0]["start_entries"] == [
        str(id_) for id_ in race_interval_start.start_entries
    ]
    assert body[0]["datatype"] == race_interval_start.datatype


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_races_by_event_id_and_raceclass(
    client: TestClient,
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
        "app.adapters.races_adapter.RacesAdapter.get_races_by_event_id_and_raceclass",
        return_value=[race_interval_start],
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    resp = client.get(f"/races?eventId={event_id}&raceclass={raceclass}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["id"] == str(race_id)
    assert body[0]["event_id"] == str(race_interval_start.event_id)
    assert body[0]["raceclass"] == raceclass
    assert body[0]["order"] == race_interval_start.order
    assert body[0]["start_time"] == race_interval_start.start_time.isoformat()
    assert body[0]["no_of_contestants"] == race_interval_start.no_of_contestants
    assert body[0]["event_id"] == str(race_interval_start.event_id)
    assert len(body[0]["start_entries"]) == len(race_interval_start.start_entries)
    assert body[0]["datatype"] == race_interval_start.datatype
    assert body[0]["id"] == str(mock_race_result.race_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_races_by_event_id_individual_sprint(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_individual_sprint: IndividualSprintRace,
) -> None:
    """Should return OK, and a body containing one race."""
    event_id = race_individual_sprint.event_id
    race_id = race_individual_sprint.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=[race_individual_sprint],
    )

    resp = client.get(f"/races?eventId={event_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["id"] == str(race_id)
    assert body[0]["raceclass"] == race_individual_sprint.raceclass
    assert body[0]["order"] == race_individual_sprint.order
    assert body[0]["start_time"] == race_individual_sprint.start_time.isoformat()
    assert body[0]["no_of_contestants"] == race_individual_sprint.no_of_contestants
    assert body[0]["event_id"] == str(race_individual_sprint.event_id)
    assert body[0]["start_entries"] == [
        str(id_) for id_ in race_individual_sprint.start_entries
    ]
    assert body[0]["round"] == race_individual_sprint.round
    assert body[0]["index"] == race_individual_sprint.index
    assert body[0]["heat"] == race_individual_sprint.heat
    assert body[0]["rule"] == race_individual_sprint.rule
    assert body[0]["datatype"] == race_individual_sprint.datatype


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_races_by_event_id_and_raceclass_individual_sprint(
    client: TestClient,
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
        "app.adapters.races_adapter.RacesAdapter.get_races_by_event_id_and_raceclass",
        return_value=[race_individual_sprint],
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    resp = client.get(f"/races?eventId={event_id}&raceclass={raceclass}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["id"] == str(race_id)
    assert body[0]["raceclass"] == raceclass
    assert body[0]["order"] == race_individual_sprint.order
    assert body[0]["start_time"] == race_individual_sprint.start_time.isoformat()
    assert body[0]["no_of_contestants"] == race_individual_sprint.no_of_contestants
    assert body[0]["event_id"] == str(race_individual_sprint.event_id)
    assert body[0]["round"] == race_individual_sprint.round
    assert body[0]["index"] == race_individual_sprint.index
    assert body[0]["heat"] == race_individual_sprint.heat
    assert body[0]["rule"] == race_individual_sprint.rule
    assert body[0]["datatype"] == race_individual_sprint.datatype
    assert body[0]["id"] == str(mock_race_result.race_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_interval_start(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return No Content."""
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        race_interval_start.model_dump(mode="json"),
        indent=4,
        sort_keys=True,
        default=str,
    )

    resp = client.put(f"/races/{race_id}", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_individual_sprint(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_individual_sprint: IndividualSprintRace,
) -> None:
    """Should return No Content."""
    race_id = race_individual_sprint.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_individual_sprint,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        race_individual_sprint.model_dump(mode="json"),
        indent=4,
        sort_keys=True,
        default=str,
    )

    resp = client.put(f"/races/{race_id}", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_races(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return OK and a valid json body."""
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_all_races",
        return_value=[race_interval_start],
    )

    resp = client.get("/races")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    races = resp.json()
    assert type(races) is list
    assert len(races) > 0
    assert races[0]["id"] == str(race_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_races_individual_sprint(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_individual_sprint: IndividualSprintRace,
) -> None:
    """Should return OK and a valid json body."""
    race_id = race_individual_sprint.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_all_races",
        return_value=[race_individual_sprint],
    )

    resp = client.get("/races")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) > 0
    assert body[0]["id"] == str(race_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return No Content."""
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=race_id,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/races/{race_id}", headers=headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT


# Bad cases


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_missing_mandatory_property(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = {"id": str(race_id)}

    resp = client.put(f"/races/{race_id}", headers=headers, json=request_body)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_different_id_in_body(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    update_body = deepcopy(race_interval_start)
    update_body.id = uuid.UUID("2b920f5c-eb82-5655-bd13-2001e5f0683e")
    request_body = dumps(
        update_body.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(f"/races/{race_id}", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_by_id_unsupported_datatype(
    client: TestClient,
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
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=NotSupportedRaceDatatypeError(
            f"Datatype {race_unsupported_datatype.datatype} not supported."
        ),
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=mock_race_result,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    resp = client.get(f"/races/{race_id}")
    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "application/json" in resp.headers["Content-Type"]


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, race_interval_start: IntervalStartRace
) -> None:
    """Should return 401 Unauthorized."""
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_id,
    )

    headers = {"Content-Type": "application/json"}

    request_body = dumps(race_interval_start, indent=4, sort_keys=True, default=str)

    resp = client.put(f"/races/{race_id}", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, race_interval_start: IntervalStartRace
) -> None:
    """Should return 401 Unauthorized."""
    race_id = race_interval_start.id
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(
            f"Race with id {race_interval_start.id} not found."
        ),
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=race_id,
    )

    resp = client.delete(f"/races/{race_id}")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


# Forbidden:
@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_unauthorized(
    client: TestClient,
    mocker: MockFixture,
    token_unsufficient_role: str,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 404 Not found."""
    race_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token_unsufficient_role}",
    }

    request_body = dumps(race_interval_start, indent=4, sort_keys=True, default=str)

    resp = client.put(f"/races/{race_id}", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.FORBIDDEN


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    race_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError("Race with id {race.id} not found."),
    )

    resp = client.get(f"/races/{race_id}")
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 404 Not found."""
    race_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(
            f"Race with id {race_interval_start.id} not found."
        ),
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        race_interval_start.model_dump(mode="json"),
        indent=4,
        sort_keys=True,
        default=str,
    )

    resp = client.put(f"/races/{race_id}", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_unknown_datatype(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: IntervalStartRace,
) -> None:
    """Should return 422 Unprocessable entity."""
    race_unknown_datatype = deepcopy(race_interval_start)
    race_unknown_datatype.datatype = "unknown"
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(
            f"Race with id {race_interval_start.id} not found."
        ),
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        race_unknown_datatype.model_dump(mode="json"),
        indent=4,
        sort_keys=True,
        default=str,
    )

    resp = client.put(
        f"/races/{race_unknown_datatype.id}", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    race_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError("Race with id {race.id} not found."),
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=None,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/races/{race_id}", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND
