"""Unit test cases for the event-service module."""
from datetime import datetime
from functools import reduce
from typing import Any, Dict, List

import pytest

from race_service.commands.raceplans_interval_start import (
    calculate_raceplan_interval_start,
)
from race_service.models import IntervalStartRace, Raceplan

# --- Interval Start ---


@pytest.fixture
async def competition_format_interval_start() -> dict:
    """A competition_format object for testing."""
    return {
        "name": "Interval Start",
        "max_no_of_contestants_in_race": 1000,
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
    }


@pytest.fixture
async def event_interval_start() -> dict:
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
async def raceclasses_interval_start() -> List[Dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclasses": ["G 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 14,
            "group": 1,
            "order": 2,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 15,
            "group": 2,
            "order": 2,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclasses": ["J 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 16,
            "group": 1,
            "order": 1,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclasses": ["J 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 17,
            "group": 2,
            "order": 1,
        },
    ]


@pytest.fixture
async def expected_raceplan_interval_start(event_interval_start: dict) -> Raceplan:
    """Create a mock raceplan object."""
    raceplan = Raceplan(event_id=event_interval_start["id"], races=list())
    raceplan.id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 62
    return raceplan


@pytest.fixture
async def expected_races_interval_start(
    competition_format_interval_start: dict,
    event_interval_start: dict,
) -> List[IntervalStartRace]:
    """Create a mock raceplan object."""
    races: List[IntervalStartRace] = []
    races.append(
        IntervalStartRace(
            id="",
            raceclass="J15",
            order=1,
            start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
            no_of_contestants=16,
            max_no_of_contestants=competition_format_interval_start[
                "max_no_of_contestants_in_race"
            ],
            event_id=event_interval_start["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IntervalStartRace(
            id="",
            raceclass="G15",
            order=2,
            start_time=datetime.fromisoformat("2021-08-31 09:08:00"),
            no_of_contestants=14,
            max_no_of_contestants=competition_format_interval_start[
                "max_no_of_contestants_in_race"
            ],
            event_id=event_interval_start["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IntervalStartRace(
            id="",
            raceclass="J16",
            order=3,
            start_time=datetime.fromisoformat("2021-08-31 09:25:00"),
            no_of_contestants=17,
            max_no_of_contestants=competition_format_interval_start[
                "max_no_of_contestants_in_race"
            ],
            event_id=event_interval_start["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IntervalStartRace(
            id="",
            raceclass="G16",
            order=4,
            start_time=datetime.fromisoformat("2021-08-31 09:33:30"),
            no_of_contestants=15,
            max_no_of_contestants=competition_format_interval_start[
                "max_no_of_contestants_in_race"
            ],
            event_id=event_interval_start["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    return races


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_raceplan_interval_start(
    competition_format_interval_start: dict,
    event_interval_start: dict,
    raceclasses_interval_start: List[dict],
    expected_raceplan_interval_start: Raceplan,
    expected_races_interval_start: List[IntervalStartRace],
) -> None:
    """Should return a tuple of Raceplan and races equal to the expected raceplan."""
    raceplan, races = await calculate_raceplan_interval_start(
        event_interval_start,
        competition_format_interval_start,
        raceclasses_interval_start,
    )

    assert type(raceplan) is Raceplan
    assert raceplan.id is None
    assert raceplan.event_id == expected_raceplan_interval_start.event_id
    assert (
        raceplan.no_of_contestants == expected_raceplan_interval_start.no_of_contestants
    )
    assert raceplan.no_of_contestants == sum(
        rc["no_of_contestants"] for rc in raceclasses_interval_start
    )
    assert len(raceplan.races) == 0
    assert len(races) == len(expected_races_interval_start)
    total_no_of_contestants = 0
    for race in races:
        assert type(race) is IntervalStartRace
        total_no_of_contestants += race.no_of_contestants
    assert total_no_of_contestants == raceplan.no_of_contestants

    # Check that the two race lists match:
    if not reduce(
        lambda x, y: x and y,
        map(lambda p, q: p == q, races, expected_races_interval_start),
        True,
    ):
        print("Calculated raceplan:")
        print(*races, sep="\n")
        print("----")
        print("Expected raceplan:")
        print(*expected_races_interval_start, sep="\n")
        raise AssertionError("Raceplan does not match expected.")
    else:
        assert 1 == 1
