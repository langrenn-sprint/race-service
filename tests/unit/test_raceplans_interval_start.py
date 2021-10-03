"""Unit test cases for the event-service module."""
from datetime import datetime
from functools import reduce
from typing import Any, List

import pytest

from race_service.commands.raceplans_interval_start import (
    calculate_raceplan_interval_start,
)
from race_service.models import Race, Raceplan

# --- Interval Start ---


@pytest.fixture
async def competition_format_interval_start() -> dict:
    """An competition_format object for testing."""
    return {
        "name": "Interval Start",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "intervals": "00:00:30",
    }


@pytest.fixture
async def event_interval_start() -> dict:
    """An competition_format object for testing."""
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
async def raceclasses_interval_start() -> List[dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclass_name": "G 15 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 14,
            "order": 2,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclass_name": "G 16 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 15,
            "order": 4,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclass_name": "J 15 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 16,
            "order": 1,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclass_name": "J 16 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 17,
            "order": 3,
        },
    ]


@pytest.fixture
async def expected_raceplan_interval_start(event_interval_start: dict) -> Raceplan:
    """Create a mock raceplan object."""
    raceplan = Raceplan(event_id=event_interval_start["id"], races=list())
    raceplan.id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 62
    raceplan.races.append(
        Race(
            raceclass="J15",
            order=1,
            start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
            no_of_contestants=16,
        )
    )
    raceplan.races.append(
        Race(
            raceclass="G15",
            order=2,
            start_time=datetime.fromisoformat("2021-08-31 09:08:00"),
            no_of_contestants=14,
        )
    )
    raceplan.races.append(
        Race(
            raceclass="J16",
            order=3,
            start_time=datetime.fromisoformat("2021-08-31 09:15:00"),
            no_of_contestants=17,
        )
    )
    raceplan.races.append(
        Race(
            raceclass="G16",
            order=4,
            start_time=datetime.fromisoformat("2021-08-31 09:23:30"),
            no_of_contestants=15,
        )
    )
    return raceplan


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_raceplan_interval_start(
    competition_format_interval_start: dict,
    event_interval_start: dict,
    raceclasses_interval_start: List[dict],
    expected_raceplan_interval_start: Raceplan,
) -> None:
    """Should return an instance of Raceplan equal to the expected raceplan."""
    raceplan = await calculate_raceplan_interval_start(
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
    assert len(raceplan.races) == len(expected_raceplan_interval_start.races)
    total_no_of_contestants = 0
    for race in raceplan.races:
        assert type(race) is Race
        total_no_of_contestants += race.no_of_contestants
    assert total_no_of_contestants == raceplan.no_of_contestants

    # Check that the two race lists match:
    if not reduce(
        lambda x, y: x and y,
        map(
            lambda p, q: p == q, raceplan.races, expected_raceplan_interval_start.races
        ),
        True,
    ):
        print("Calculated raceplan:")
        print(*raceplan.races, sep="\n")
        print("----")
        print("Expected raceplan:")
        print(*expected_raceplan_interval_start.races, sep="\n")
        raise AssertionError("Raceplan does not match expected.")
    else:
        assert 1 == 1
