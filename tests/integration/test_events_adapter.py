"""Integration test cases for the events adapter get_raceclass_by_name method."""

from typing import Any

import pytest
from pytest_mock import MockFixture

from race_service.adapters import (
    EventsAdapter,
    RaceclassNotFoundError,
)


@pytest.fixture
async def raceclass() -> dict[str, Any]:
    """Raceclass object for testing."""
    return {
        "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "G15",
        "ageclasses": ["G 15 år"],
        "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "no_of_contestants": 15,
        "ranking": True,
        "group": 1,
        "order": 2,
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_raceclass_by_name_via_mocker(
    mocker: MockFixture,
    raceclass: dict[str, Any],
) -> None:
    """Should return a single raceclass when mocked."""
    event_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    token = "test_token"  # noqa: S105
    name = "G15"

    # Mock the get_raceclass_by_name method
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclass_by_name",
        return_value=raceclass,
    )

    result = await EventsAdapter.get_raceclass_by_name(token, event_id, name)

    assert result == raceclass
    assert result["name"] == name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_raceclass_by_name_not_found_via_mocker(
    mocker: MockFixture,
) -> None:
    """Should raise RaceclassNotFoundError when raceclass is not found."""
    event_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    token = "test_token"  # noqa: S105
    name = "NonExistentClass"

    # Mock the get_raceclass_by_name method to raise an exception
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclass_by_name",
        side_effect=RaceclassNotFoundError(
            f'Raceclass "{name}" not found for event {event_id}.'
        ),
    )

    with pytest.raises(RaceclassNotFoundError) as exc_info:
        await EventsAdapter.get_raceclass_by_name(token, event_id, name)

    assert f'Raceclass "{name}" not found' in str(exc_info.value)
    assert event_id in str(exc_info.value)
