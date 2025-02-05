"""Integration test cases for the startlists route."""

import os
import uuid
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from typing import Any

import jwt
import pytest
from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
from pytest_mock import MockFixture

from race_service.models import IndividualSprintRace, Raceplan, Startlist

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")

MAX_NO_OF_CONTESTANTS_IN_raceclass = 80
MAX_NO_OF_CONTESTANTS_IN_RACE = 10


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
async def request_body() -> dict:
    """Create a mock request_body object."""
    return {"event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95"}


EVENT = {
    "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
    "name": "Oslo Skagen sprint",
    "competition_format": "Individual Sprint",
    "date_of_event": "2021-08-31",
    "time_of_event": "09:00:00",
    "organiser": "Lyn Ski",
    "webpage": "https://example.com",
    "information": "Testarr for å teste den nye løysinga.",
}


@pytest.fixture
async def event_individual_sprint() -> dict[str, Any]:
    """An event object for testing."""
    return EVENT


@pytest.fixture
async def competition_format() -> dict[str, Any]:
    """A competition-format for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_groups": "00:15:00",
        "time_between_rounds": "00:10:00",
        "time_between_heats": "00:02:30",
        "rounds_ranked_classes": ["Q", "S", "F"],
        "rounds_non_ranked_classes": ["R1", "R2"],
        "max_no_of_contestants_in_raceclass": MAX_NO_OF_CONTESTANTS_IN_raceclass,
        "max_no_of_contestants_in_race": MAX_NO_OF_CONTESTANTS_IN_RACE,
        "datatype": "individual_sprint",
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
            "ranking": False,
            "group": 2,
            "order": 1,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "ranking": True,
            "group": 1,
            "order": 1,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclasses": ["J 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "ranking": False,
            "group": 2,
            "order": 2,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclasses": ["J 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "ranking": True,
            "group": 1,
            "order": 2,
        },
    ]


RACES: list[IndividualSprintRace] = [
    IndividualSprintRace(
        id="1",
        order=1,
        raceclass="G16",
        round="Q",
        index="",
        heat=1,
        start_time=datetime.fromisoformat("2021-08-31 09:07:30"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="individual_sprint",
    ),
    IndividualSprintRace(
        id="2",
        order=2,
        raceclass="J16",
        round="Q",
        index="",
        heat=1,
        start_time=datetime.fromisoformat("2021-08-31 09:05:00"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="individual_sprint",
    ),
    IndividualSprintRace(
        id="3",
        order=3,
        raceclass="G15",
        round="R1",
        index="",
        heat=1,
        start_time=datetime.fromisoformat("2021-08-31 09:02:30"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="individual_sprint",
    ),
    IndividualSprintRace(
        id="4",
        order=4,
        raceclass="J15",
        round="R1",
        index="",
        heat=1,
        start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="individual_sprint",
    ),
    IndividualSprintRace(
        id="5",
        order=5,
        raceclass="G15",
        round="R2",
        index="",
        heat=1,
        start_time=datetime.fromisoformat("2021-08-31 09:02:30"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="individual_sprint",
    ),
    IndividualSprintRace(
        id="6",
        order=6,
        raceclass="J15",
        round="R2",
        index="",
        heat=1,
        start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
        no_of_contestants=2,
        max_no_of_contestants=MAX_NO_OF_CONTESTANTS_IN_RACE,
        event_id=EVENT["id"],
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        datatype="individual_sprint",
    ),
]

RACEPLAN = Raceplan(
    event_id=EVENT["id"],
    id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
    no_of_contestants=8,
    races=[race.id for race in RACES],
)


@pytest.fixture
async def raceplan_individual_sprint(event_individual_sprint: dict) -> Raceplan:
    """Create a mock raceplan object."""
    return RACEPLAN


@pytest.fixture
async def contestants(
    event_individual_sprint: dict, raceplan_individual_sprint: Raceplan
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
            "event_id": event_individual_sprint["id"],
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
            "event_id": event_individual_sprint["id"],
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
            "event_id": event_individual_sprint["id"],
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
            "event_id": event_individual_sprint["id"],
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
            "event_id": event_individual_sprint["id"],
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
            "event_id": event_individual_sprint["id"],
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
            "event_id": event_individual_sprint["id"],
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
            "event_id": event_individual_sprint["id"],
        },
    ]


def get_race_by_id(db: Any, id_: str) -> IndividualSprintRace:
    """Mock function to look up correct race from list."""
    return next(race for race in RACES if race.id == id_)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_individual_sprint: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_individual_sprint: Raceplan,
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 201 Created and location header."""
    startlist_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=startlist_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=startlist_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        side_effect=str(uuid.uuid4()),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=Startlist(
            id=startlist_id,
            event_id=event_individual_sprint["id"],
            start_entries=[],
            no_of_contestants=0,
        ),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_individual_sprint],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=RACES,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=get_race_by_id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.CREATED
        assert f"/startlists/{startlist_id}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_wrong_no_of_contestants_in_races(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_individual_sprint: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_individual_sprint: Raceplan,
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    startlist_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan_races_with_wrong_no_of_contestants = deepcopy(raceplan_individual_sprint)
    races = deepcopy(RACES)
    race_with_wrong_number_of_contestants = races[0]
    race_with_wrong_number_of_contestants.no_of_contestants = 100000
    raceplan_races_with_wrong_no_of_contestants.races[0] = (
        race_with_wrong_number_of_contestants.id
    )

    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=startlist_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=startlist_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        side_effect=str(uuid.uuid4()),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=Startlist(
            id=startlist_id,
            event_id=event_individual_sprint["id"],
            start_entries=[],
            no_of_contestants=0,
        ),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_races_with_wrong_no_of_contestants],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=get_race_by_id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST
        body = await resp.json()
        assert (
            "Number of contestants in event does not match sum of contestants in races"
            in body["detail"]
        )
