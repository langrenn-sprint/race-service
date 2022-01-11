"""Unit test cases for the event-service module."""
from datetime import datetime
from functools import reduce
from typing import Any, Dict, List

import pytest

from race_service.commands.raceplans_individual_sprint import (
    calculate_raceplan_individual_sprint,
)
from race_service.models import IndividualSprintRace, Raceplan

# --- Individual Sprint ---


@pytest.fixture
async def competition_format_individual_sprint() -> dict:
    """A competition_format object for testing."""
    return {
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_groups": "00:10:00",
        "time_between_rounds": "00:10:00",
        "time_between_heats": "00:02:30",
        "max_no_of_contestants_in_raceclass": 80,
        "max_no_of_contestants_in_race": 10,
        "datatype": "individual_sprint",
    }


@pytest.fixture
async def event_individual_sprint() -> dict:
    """An event object for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint",
        "competition_format": "Individual Sprint",
        "date_of_event": "2021-09-29",
        "time_of_event": "09:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def raceclasses_individual_sprint() -> List[Dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclass_name": "J 15 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 27,
            "group": 1,
            "order": 1,
        },
    ]


@pytest.fixture
async def expected_raceplan_individual_sprint(
    event_individual_sprint: dict,
) -> Raceplan:
    """Create a mock raceplan object."""
    raceplan = Raceplan(event_id=event_individual_sprint["id"], races=list())
    raceplan.id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 27

    return raceplan


@pytest.fixture
async def expected_races_individual_sprint(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
) -> List[IndividualSprintRace]:
    """Create a mock raceplan object."""
    races: List[IndividualSprintRace] = []
    races.append(
        IndividualSprintRace(
            id="",
            order=1,
            raceclass="J15",
            round="Q",
            index="",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": float("inf")}},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=2,
            raceclass="J15",
            round="Q",
            index="",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": float("inf")}},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=3,
            raceclass="J15",
            round="Q",
            index="",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": float("inf")}},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=4,
            raceclass="J15",
            round="Q",
            index="",
            heat=4,
            start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": float("inf")}},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=5,
            raceclass="J15",
            round="S",
            index="C",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"F": {"C": 4}},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=6,
            raceclass="J15",
            round="S",
            index="C",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
            no_of_contestants=5,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"F": {"C": 4}},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=7,
            raceclass="J15",
            round="S",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
            no_of_contestants=8,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"F": {"A": 4, "B": float("inf")}},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=8,
            raceclass="J15",
            round="S",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:25:00"),
            no_of_contestants=8,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"F": {"A": 4, "B": float("inf")}},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=9,
            raceclass="J15",
            round="F",
            index="C",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:35:00"),
            no_of_contestants=8,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=10,
            raceclass="J15",
            round="F",
            index="B",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:37:30"),
            no_of_contestants=8,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="",
            order=11,
            raceclass="J15",
            round="F",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:40:00"),
            no_of_contestants=8,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={},
            event_id=event_individual_sprint["id"],
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )

    return races


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_raceplan_individual_sprint(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
    raceclasses_individual_sprint: List[dict],
    expected_raceplan_individual_sprint: Raceplan,
    expected_races_individual_sprint: List[IndividualSprintRace],
) -> None:
    """Should return a tuple of Raceplan and races equal to the expected raceplan."""
    raceplan, races = await calculate_raceplan_individual_sprint(
        event_individual_sprint,
        competition_format_individual_sprint,
        raceclasses_individual_sprint,
    )

    assert type(raceplan) is Raceplan
    assert raceplan.id is None
    assert raceplan.event_id == expected_raceplan_individual_sprint.event_id
    # Check that no_of_contestants corresponds to the number given in raceclasses:
    assert (
        raceplan.no_of_contestants
        == expected_raceplan_individual_sprint.no_of_contestants
    )
    # Check that all the contestants have been given a Quarterfinal:
    assert (
        sum(race.no_of_contestants for race in races if race.round == "Q")
        == raceplan.no_of_contestants
    )

    # Check that there are correct number of races:
    assert len(raceplan.races) == 0
    assert len(races) == len(expected_races_individual_sprint)
    # Check that the two race lists match:
    if not reduce(
        lambda x, y: x and y,
        map(
            lambda p, q: p == q,
            races,
            expected_raceplan_individual_sprint.races,
        ),
        True,
    ):
        print("Calculated raceplan:")
        print(*races, sep="\n")
        print("----")
        print("Expected raceplan:")
        print(*expected_races_individual_sprint, sep="\n")
        raise AssertionError("Raceplan does not match expected.")
    else:
        assert 1 == 1
