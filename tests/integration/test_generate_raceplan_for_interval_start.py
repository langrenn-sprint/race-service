"""Integration test cases for the raceplans route."""

import os
import uuid
from http import HTTPStatus
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app.models import Raceplan


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


@pytest.fixture
async def event() -> dict[str, Any]:
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
async def competition_format() -> dict[str, Any]:
    """A competition-format for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Interval Start",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
        "max_no_of_contestants_in_raceclass": 10000,
        "max_no_of_contestants_in_race": 10000,
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
@pytest.mark.asyncio
async def test_generate_raceplan_for_event(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    request_body: dict,
) -> None:
    """Should return 201 Created, location header."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    create_raceplan = mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=raceplan_id,
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        side_effect=lambda id_: Raceplan(
            id=id_, event_id=event["id"], races=[], no_of_contestants=0
        ),
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.create_race",
        side_effect=str(uuid.uuid4()),
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
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
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=races,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        "/raceplans/generate-raceplan-for-event", headers=headers, json=request_body
    )
    assert resp.status_code == HTTPStatus.CREATED
    created_raceplan = create_raceplan.call_args.args[0]
    assert f"/raceplans/{created_raceplan.id}" in resp.headers["Location"]


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
