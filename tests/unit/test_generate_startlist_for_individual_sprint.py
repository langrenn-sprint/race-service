"""Unit test cases for the startlist_commands module."""
from datetime import datetime
from functools import reduce
from typing import List

import pytest

from race_service.commands.startlists_commands import (
    generate_startlist_for_individual_sprint,
)
from race_service.models import IndividualSprintRace, Raceplan, StartEntry, Startlist

# --- Individual Sprint ---


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_startlist_for_individual_sprint(
    event_individual_sprint: dict,
    competition_format_individual_sprint: dict,
    raceclasses: List[dict],
    raceplan_individual_sprint: Raceplan,
    contestants: List[dict],
    expected_startlist_individual_sprint: Startlist,
) -> None:
    """Should return an instance of Raceplan equal to the expected raceplan."""
    startlist = await generate_startlist_for_individual_sprint(
        event_individual_sprint,
        competition_format_individual_sprint,
        raceclasses,
        raceplan_individual_sprint,
        contestants,
    )

    assert type(startlist) is Startlist
    assert startlist.id is None
    assert startlist.event_id == expected_startlist_individual_sprint.event_id
    assert (
        startlist.no_of_contestants
        == expected_startlist_individual_sprint.no_of_contestants
    )
    assert startlist.no_of_contestants == sum(
        rc["no_of_contestants"] for rc in raceclasses
    )
    assert len(startlist.start_entries) == len(
        expected_startlist_individual_sprint.start_entries
    )
    no_of_start_entries = 0
    for start_entry in startlist.start_entries:
        assert type(start_entry) is StartEntry
        no_of_start_entries += 1
    assert no_of_start_entries == startlist.no_of_contestants

    # Check that the two race lists match:
    if not reduce(
        lambda x, y: x and y,
        map(
            lambda p, q: p == q,
            startlist.start_entries,
            expected_startlist_individual_sprint.start_entries,
        ),
        True,
    ):
        print("Calculated startlist:")
        print(*startlist.start_entries, sep="\n")
        print("----")
        print("Expected startlist:")
        print(*expected_startlist_individual_sprint.start_entries, sep="\n")
        raise AssertionError("Startlist does not match expected.")
    else:
        assert 1 == 1


# Fixtures:
@pytest.fixture
async def competition_format_individual_sprint() -> dict:
    """An competition_format object for testing."""
    return {
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Individual Sprint",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
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
async def raceclasses(
    event_individual_sprint: dict, contestants: List[dict]
) -> List[dict]:
    """Create a mock raceclasses object."""
    raceclasses: List[dict] = []
    raceclasses.append(
        {
            "name": "J15",
            "group": 1,
            "order": 1,
            "ageclass_name": "J 15 år",
            "no_of_contestants": 27,
            "event_id": event_individual_sprint["id"],
            "distance": "5km",
        }
    )
    return raceclasses


@pytest.fixture
async def raceplan_individual_sprint(event_individual_sprint: dict) -> Raceplan:
    """Create a mock raceplan object."""
    raceplan = Raceplan(event_id=event_individual_sprint["id"], races=list())
    raceplan.id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 27
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=1,
            raceclass="J15",
            round="Q",
            index="",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=7,
            rule={"S": {"A": 4, "C": float("inf")}},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=2,
            raceclass="J15",
            round="Q",
            index="",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=7,
            rule={"S": {"A": 4, "C": float("inf")}},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=3,
            raceclass="J15",
            round="Q",
            index="",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
            no_of_contestants=7,
            rule={"S": {"A": 4, "C": float("inf")}},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=4,
            raceclass="J15",
            round="Q",
            index="",
            heat=4,
            start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
            no_of_contestants=6,
            rule={"S": {"A": 4, "C": float("inf")}},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=5,
            raceclass="J15",
            round="S",
            index="C",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
            no_of_contestants=6,
            rule={"F": {"C": 4}},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=6,
            raceclass="J15",
            round="S",
            index="C",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
            no_of_contestants=5,
            rule={"F": {"C": 4}},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=7,
            raceclass="J15",
            round="S",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
            no_of_contestants=8,
            rule={"F": {"A": 4, "B": float("inf")}},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=8,
            raceclass="J15",
            round="S",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:25:00"),
            no_of_contestants=8,
            rule={"F": {"A": 4, "B": float("inf")}},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=9,
            raceclass="J15",
            round="F",
            index="C",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:35:00"),
            no_of_contestants=8,
            rule={},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=10,
            raceclass="J15",
            round="F",
            index="B",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:37:30"),
            no_of_contestants=8,
            rule={},
        )
    )
    raceplan.races.append(
        IndividualSprintRace(
            id="",
            order=11,
            raceclass="J15",
            round="F",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:40:00"),
            no_of_contestants=8,
            rule={},
        )
    )
    assert (
        sum(race.no_of_contestants for race in raceplan.races if race.round == "Q")
        == raceplan.no_of_contestants
    )

    return raceplan


@pytest.fixture
async def contestants(
    event_individual_sprint: dict, raceplan_individual_sprint: Raceplan
) -> List[dict]:
    """Create a mock contestant list object."""
    return [
        {
            "bib": 1,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 2,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 3,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 4,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 5,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 6,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 7,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 8,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 9,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 10,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 11,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 12,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 13,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 14,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 15,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 16,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 17,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 18,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 19,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 20,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 21,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 22,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 23,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 24,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 25,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 26,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 27,
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
    ]


@pytest.fixture
async def expected_startlist_individual_sprint(
    event_individual_sprint: dict, raceplan_individual_sprint: Raceplan
) -> Startlist:
    """Create a mock raceplan object."""
    startlist = Startlist(
        event_id=event_individual_sprint["id"],
        no_of_contestants=raceplan_individual_sprint.no_of_contestants,
        start_entries=list(),
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=1,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=2,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=3,
            starting_position=3,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=4,
            starting_position=4,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=5,
            starting_position=5,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=6,
            starting_position=6,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=7,
            starting_position=7,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=8,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=9,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=10,
            starting_position=3,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=11,
            starting_position=4,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=12,
            starting_position=5,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=13,
            starting_position=6,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=14,
            starting_position=7,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=15,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=16,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=17,
            starting_position=3,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=18,
            starting_position=4,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=19,
            starting_position=5,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=20,
            starting_position=6,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=21,
            starting_position=7,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=22,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=23,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=24,
            starting_position=3,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=25,
            starting_position=4,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=26,
            starting_position=5,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    startlist.start_entries.append(
        StartEntry(
            id="",
            race_id="",
            bib=27,
            starting_position=6,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    return startlist
