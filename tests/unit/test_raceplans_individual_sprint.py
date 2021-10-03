"""Unit test cases for the event-service module."""
from datetime import datetime
from functools import reduce
from typing import Any, List

import pytest

from race_service.commands.raceplans_individual_sprint import (
    calculate_raceplan_individual_sprint,
)
from race_service.models import IndividualSprintRace, Raceplan

# --- Individual Sprint ---


@pytest.fixture
async def competition_format_individual_sprint() -> dict:
    """An competition_format object for testing."""
    return {
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
    }


@pytest.fixture
async def event_individual_sprint() -> dict:
    """An competition_format object for testing."""
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
async def raceclasses_individual_sprint() -> List[dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclass_name": "J 15 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 27,
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
    raceplan.races.append(
        IndividualSprintRace(
            order=1,
            raceclass="J15",
            round="Q",
            index="",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=7,
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            order=2,
            raceclass="J15",
            round="Q",
            index="",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=7,
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            order=3,
            raceclass="J15",
            round="Q",
            index="",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
            no_of_contestants=7,
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            order=4,
            raceclass="J15",
            round="Q",
            index="",
            heat=4,
            start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
            no_of_contestants=6,
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            order=5,
            raceclass="J15",
            round="S",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
            no_of_contestants=7,
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            order=6,
            raceclass="J15",
            round="S",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
            no_of_contestants=6,
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            order=7,
            raceclass="J15",
            round="F",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:30:00"),
            no_of_contestants=6,
        )
    )

    return raceplan


# @pytest.mark.skip(reason="no way of currently testing this")
@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_raceplan_individual_sprint(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
    raceclasses_individual_sprint: List[dict],
    expected_raceplan_individual_sprint: Raceplan,
) -> None:
    """Should return an instance of Raceplan equal to the expected raceplan."""
    raceplan = await calculate_raceplan_individual_sprint(
        event_individual_sprint,
        competition_format_individual_sprint,
        raceclasses_individual_sprint,
    )

    assert type(raceplan) is Raceplan
    assert raceplan.id is None
    assert raceplan.event_id == expected_raceplan_individual_sprint.event_id
    # Check that no_of_contestants corresponds to the number given in raceclasses:
    assert raceplan.no_of_contestants == sum(
        rc["no_of_contestants"] for rc in raceclasses_individual_sprint
    )
    assert (
        raceplan.no_of_contestants
        == expected_raceplan_individual_sprint.no_of_contestants
    )
    # Check that there are correct number of races:
    assert len(raceplan.races) == len(expected_raceplan_individual_sprint.races)
    # Check that all the contestants have been given a Quarterfinal:
    total_no_of_contestants_in_quarterfinals = 0
    for race in raceplan.races:
        assert type(race) is IndividualSprintRace
        if race.round == "Q":
            total_no_of_contestants_in_quarterfinals += race.no_of_contestants
    assert total_no_of_contestants_in_quarterfinals == raceplan.no_of_contestants

    # Check that the two race lists match:
    if not reduce(
        lambda x, y: x and y,
        map(
            lambda p, q: p == q,
            raceplan.races,
            expected_raceplan_individual_sprint.races,
        ),
        True,
    ):
        print("Calculated raceplan:")
        print(*raceplan.races, sep="\n")
        print("----")
        print("Expected raceplan:")
        print(*expected_raceplan_individual_sprint.races, sep="\n")
        raise AssertionError("Raceplan does not match expected.")
    else:
        print(*raceplan.races, sep="\n")
        assert 1 == 1
