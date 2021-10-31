"""Integration test cases for the startlists route."""
from datetime import datetime
import os
from typing import Any, List

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
import jwt
from multidict import MultiDict
import pytest
from pytest_mock import MockFixture


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.fixture
async def request_body() -> dict:
    """Create a mock request_body object."""
    return {"event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95"}


@pytest.fixture
async def event_individual_sprint() -> dict[str, Any]:
    """An event object for testing."""
    return {
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
async def format_configuration() -> dict[str, Any]:
    """An format configuration for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_groups": "00:15:00",
        "time_between_rounds": "00:10:00",
        "time_between_heats": "00:02:30",
        "max_no_of_contestants": 80,
        "datatype": "individual_sprint",
    }


@pytest.fixture
async def raceclasses() -> List[dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclass_name": "G 15 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 2,
            "order": 1,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclass_name": "G 16 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 1,
            "order": 1,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclass_name": "J 15 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 2,
            "order": 2,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclass_name": "J 16 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 1,
            "order": 2,
        },
    ]


@pytest.fixture
async def raceplan_individual_sprint(event_individual_sprint: dict) -> dict:
    """Create a mock raceplan object."""
    return {
        "event_id": event_individual_sprint["id"],
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "no_of_contestants": 8,
        "races": [
            {
                "id": "1",
                "order": 1,
                "raceclass": "J15",
                "round": "Q",
                "index": "",
                "heat": 1,
                "start_time": datetime.fromisoformat("2021-08-31 09:00:00"),
                "no_of_contestants": 2,
                "event_id": event_individual_sprint["id"],
                "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
                "startlist_id": "",
                "datatype": "individual_sprint",
            },
            {
                "id": "2",
                "order": 2,
                "raceclass": "G15",
                "round": "Q",
                "index": "",
                "heat": 1,
                "start_time": datetime.fromisoformat("2021-08-31 09:02:30"),
                "no_of_contestants": 2,
                "event_id": event_individual_sprint["id"],
                "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
                "startlist_id": "",
                "datatype": "individual_sprint",
            },
            {
                "id": "3",
                "order": 3,
                "raceclass": "J16",
                "round": "Q",
                "index": "",
                "heat": 1,
                "start_time": datetime.fromisoformat("2021-08-31 09:05:00"),
                "no_of_contestants": 2,
                "event_id": event_individual_sprint["id"],
                "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
                "startlist_id": "",
                "datatype": "individual_sprint",
            },
            {
                "id": "4",
                "order": 4,
                "raceclass": "G16",
                "round": "Q",
                "index": "",
                "heat": 1,
                "start_time": datetime.fromisoformat("2021-08-31 09:07:30"),
                "no_of_contestants": 2,
                "event_id": event_individual_sprint["id"],
                "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
                "startlist_id": "",
                "datatype": "individual_sprint",
            },
        ],
    }


@pytest.fixture
async def contestants(
    event_individual_sprint: dict, raceplan_individual_sprint: dict
) -> List[dict]:
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


@pytest.mark.integration
async def test_generate_startlist_for_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_individual_sprint: dict,
    format_configuration: dict,
    raceclasses: List[dict],
    raceplan_individual_sprint: dict,
    contestants: List[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    RACEPLAN_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_format_configuration",
        return_value=format_configuration,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_event_id",
        return_value=[raceplan_individual_sprint],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=raceplan_individual_sprint["races"],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=raceplan_individual_sprint["races"],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == 201
        assert f"/startlists/{RACEPLAN_ID}" in resp.headers[hdrs.LOCATION]
