"""Integration test cases for the race_results service."""

from datetime import datetime

import pytest
from pytest_mock import MockFixture

from app.adapters import TimeEventNotFoundError
from app.models import TimeEvent
from app.services import TimeEventsService


@pytest.fixture
async def time_event_mock() -> TimeEvent:
    """Create a time-event object."""
    return TimeEvent(
        id="1ba641c0-ed88-5934-9b13-667d34430228",
        bib=1,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        race="race_name",
        rank=1,
        next_race="semi_name1",
        next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
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
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )

    assert time_event_mock.id
    with pytest.raises(TimeEventNotFoundError):
        await TimeEventsService.delete_time_event(id_=time_event_mock.id)
