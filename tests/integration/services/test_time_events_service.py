"""Integration test cases for the race_results service."""

from datetime import datetime

import pytest
from pytest_mock import MockFixture

from race_service.adapters import TimeEventNotFoundError
from race_service.models import TimeEvent
from race_service.services import TimeEventsService


@pytest.fixture
async def time_event_mock() -> TimeEvent:
    """Create a time-event object."""
    return TimeEvent(
        id="time_event_1",
        bib=1,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        race_id="race_1",
        race="race_name",
        rank=1,
        next_race="semi_name1",
        next_race_id="semi_1",
        next_race_position=1,
        status="OK",
        changelog=[],
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_time_event_not_found(
    mocker: MockFixture,
    time_event_mock: TimeEvent,
) -> None:
    """Should raise RaceNotFoundError."""
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )

    assert time_event_mock.id
    with pytest.raises(TimeEventNotFoundError):
        await TimeEventsService.delete_time_event(db=None, id_=time_event_mock.id)
