"""Integration test cases for the raceplans route."""
import os
from typing import Any, Dict, List
import uuid

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
import jwt
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
async def event() -> Dict[str, Any]:
    """An event object for testing."""
    return {
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
async def competition_format() -> Dict[str, Any]:
    """A competition-format for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Interval Start",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
        "max_no_of_contestants_in_raceclass": 10000,
        "max_no_of_contestants_in_race": 10000,
        "timezone": "Europe/Oslo",
    }


@pytest.fixture
async def raceclasses() -> List[Dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclasses": ["G 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 15,
            "ranking": True,
            "group": 2,
            "order": 1,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 16,
            "ranking": True,
            "group": 1,
            "order": 1,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclasses": ["J 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 17,
            "ranking": True,
            "group": 2,
            "order": 2,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclasses": ["J 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 18,
            "ranking": True,
            "group": 1,
            "order": 2,
        },
    ]


@pytest.mark.integration
async def test_generate_raceplan_for_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: List[dict],
    request_body: dict,
) -> None:
    """Should return 201 Created, location header."""
    RACEPLAN_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value={"id": RACEPLAN_ID},
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        side_effect=str(uuid.uuid4()),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
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
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=races,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8080/authorize", status=204)

        resp = await client.post(
            "/raceplans/generate-raceplan-for-event", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert f"/raceplans/{RACEPLAN_ID}" in resp.headers[hdrs.LOCATION]


races = [
    {
        "id": "",
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T09:00:00",
        "max_no_of_contestants": 10000,
        "no_of_contestants": 16,
        "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "raceplan_id": "",
        "start_entries": [],
        "results": {},
        "datatype": "interval_start",
    },
    {
        "id": "",
        "raceclass": "J16",
        "order": 2,
        "start_time": "2021-08-31T09:08:00",
        "max_no_of_contestants": 10000,
        "no_of_contestants": 18,
        "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "raceplan_id": "",
        "start_entries": [],
        "results": {},
        "datatype": "interval_start",
    },
    {
        "id": "",
        "raceclass": "G15",
        "order": 3,
        "start_time": "2021-08-31T09:27:00",
        "max_no_of_contestants": 10000,
        "no_of_contestants": 15,
        "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "raceplan_id": "",
        "start_entries": [],
        "results": {},
        "datatype": "interval_start",
    },
    {
        "id": "",
        "raceclass": "J15",
        "order": 4,
        "start_time": "2021-08-31T09:34:30",
        "max_no_of_contestants": 10000,
        "no_of_contestants": 17,
        "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "raceplan_id": "",
        "start_entries": [],
        "results": {},
        "datatype": "interval_start",
    },
]
