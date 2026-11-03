"""Integration test cases for the startlists route."""

import os
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app.models import IntervalStartRace, Raceplan, Startlist

MAX_NO_OF_CONTESTANTS_IN_raceclass = 80
MAX_NO_OF_CONTESTANTS_IN_RACE = 10


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
async def request_body() -> dict:
    """Create a mock request_body object."""
    return {"event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95"}


EVENT = {
    "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
    "name": "Oslo Skagen sprint",
    "competition_format": "Interval Start",
    "date_of_event": "2021-08-31",
    "time_of_event": "09:00:00",
    "organiser": "Lyn Ski",
    "webpage": "https://example.com",
    "information": "Testarr for å teste den nye løysinga.",
}


@pytest.fixture
async def event_interval_start() -> dict[str, Any]:
    """An event object for testing."""
    return EVENT


@pytest.fixture
async def competition_format() -> dict[str, Any]:
    """An competition-format for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Interval Start",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
        "max_no_of_contestants_in_raceclass": MAX_NO_OF_CONTESTANTS_IN_raceclass,
        "max_no_of_contestants_in_race": MAX_NO_OF_CONTESTANTS_IN_RACE,
    }


@pytest.fixture
async def raceclasses() -> list[dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclasses": ["G 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 2,
            "order": 1,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 1,
            "order": 1,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclasses": ["J 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 2,
            "order": 2,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclasses": ["J 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 1,
            "order": 2,
        },
    ]


RACES: list[IntervalStartRace] = [
    IntervalStartRace(
        id="311ad0e6-2c39-506d-b2f9-1c317c38b50b",
        raceclass="J15",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="interval_start",
    ),
    IntervalStartRace(
        id="ce565303-7508-5221-9f88-4630b31cf3dc",
        raceclass="G15",
        order=2,
        start_time=datetime.fromisoformat("2021-08-31 09:01:00"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="interval_start",
    ),
    IntervalStartRace(
        id="0d1a98aa-7a4a-589a-a6f6-2c652c454901",
        raceclass="J16",
        order=3,
        start_time=datetime.fromisoformat("2021-08-31 09:02:00"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="interval_start",
    ),
    IntervalStartRace(
        id="0b59eb8e-e5b1-567e-9713-4caf1a3b155f",
        raceclass="G16",
        order=4,
        start_time=datetime.fromisoformat("2021-08-31 09:03:00"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="interval_start",
    ),
]

RACEPLAN = Raceplan(
    event_id=EVENT["id"],
    id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
    no_of_contestants=8,
    races=[race.id for race in RACES],
)


@pytest.fixture
async def raceplan_interval_start(event_interval_start: dict) -> Raceplan:
    """Create a mock raceplan object."""
    return RACEPLAN


@pytest.fixture
async def contestants(
    event_interval_start: dict, raceplan_interval_start: Raceplan
) -> list[dict]:
    """Create a mock contestant list object."""
    return [
        {
            "bib": 1,
            "first_name": "Cont E.",
            "last_name": "Stant",
            "birth_date": "1970-01-01",
            "gender": "K",
            "ageclass": "J 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": EVENT["id"],
        },
        {
            "bib": 2,
            "first_name": "Conte E.",
            "last_name": "Stante",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "J 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": EVENT["id"],
        },
        {
            "bib": 3,
            "first_name": "Conta E.",
            "last_name": "Stanta",
            "birth_date": "1970-01-01",
            "gender": "K",
            "ageclass": "G 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": EVENT["id"],
        },
        {
            "bib": 4,
            "first_name": "Conti E.",
            "last_name": "Stanti",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "G 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": EVENT["id"],
        },
        {
            "bib": 5,
            "first_name": "AContA E.",
            "last_name": "AStanta",
            "birth_date": "1970-01-01",
            "gender": "K",
            "ageclass": "J 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": EVENT["id"],
        },
        {
            "bib": 6,
            "first_name": "AConte E.",
            "last_name": "AStante",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "J 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": EVENT["id"],
        },
        {
            "bib": 7,
            "first_name": "Contas E.",
            "last_name": "Stantas",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "G 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": EVENT["id"],
        },
        {
            "bib": 8,
            "first_name": "Contus E.",
            "last_name": "Stantus",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "G 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": EVENT["id"],
        },
    ]


def get_race_by_id(id_: str) -> IntervalStartRace:
    """Mock function to look up correct race from list."""
    return next(race for race in RACES if str(race.id) == str(id_))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_interval_start: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 201 Created, location header."""
    startlist_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    create_startlist = mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=startlist_id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        side_effect=str(uuid.uuid4()),
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=lambda id_: Startlist(
            id=id_,
            event_id=event_interval_start["id"],
            start_entries=[],
            no_of_contestants=0,
        ),
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_interval_start,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=RACES,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=get_race_by_id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        "/startlists/generate-startlist-for-event",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == HTTPStatus.CREATED
    created_startlist = create_startlist.call_args.args[0]
    assert f"/startlists/{created_startlist.id}" in resp.headers["Location"]
