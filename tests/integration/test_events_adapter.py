"""Integration test cases for the events adapter."""

import os
from http import HTTPStatus
from typing import Any

import pytest
from aioresponses import aioresponses
from dotenv import load_dotenv

from race_service.adapters import (
    EventsAdapter,
    RaceclassNotFoundError,
)

load_dotenv()

EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT")


@pytest.fixture
async def raceclasses() -> list[dict[str, Any]]:
    """Raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclasses": ["G 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 15,
            "ranking": True,
            "group": 1,
            "order": 2,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 16,
            "ranking": True,
            "group": 1,
            "order": 4,
        },
    ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_raceclass_by_name_success(raceclasses: list[dict]) -> None:
    """Should return a single raceclass when found."""
    event_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    token = "test_token"
    name = "G15"

    url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/raceclasses?name={name}"

    with aioresponses() as m:
        m.get(url, status=HTTPStatus.OK, payload=[raceclasses[0]])

        result = await EventsAdapter.get_raceclass_by_name(token, event_id, name)

        assert result == raceclasses[0]
        assert result["name"] == name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_raceclass_by_name_not_found() -> None:
    """Should raise RaceclassNotFoundError when raceclass is not found."""
    event_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    token = "test_token"
    name = "NonExistentClass"

    url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/raceclasses?name={name}"

    with aioresponses() as m:
        m.get(url, status=HTTPStatus.OK, payload=[])

        with pytest.raises(RaceclassNotFoundError) as exc_info:
            await EventsAdapter.get_raceclass_by_name(token, event_id, name)

        assert f'Raceclass "{name}" not found' in str(exc_info.value)
        assert event_id in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_raceclass_by_name_server_error() -> None:
    """Should raise HTTPInternalServerError when server returns error."""
    event_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    token = "test_token"
    name = "G15"

    url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/raceclasses?name={name}"

    with aioresponses() as m:
        m.get(url, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        with pytest.raises(Exception) as exc_info:
            await EventsAdapter.get_raceclass_by_name(token, event_id, name)

        assert "Got unknown status from events service" in str(exc_info.value)
