"""Unit test cases for the startlist_commands module."""
from datetime import datetime
from functools import reduce
from typing import List

import pytest

from race_service.commands.startlists_commands import (
    generate_startlist_for_individual_sprint,
)
from race_service.models import IndividualSprintRace, Raceplan, StartEntry, Startlist

# --- Individual Sprint, ranked. ---


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_startlist_for_individual_sprint(
    event_individual_sprint: dict,
    competition_format_individual_sprint: dict,
    raceclasses: List[dict],
    raceplan_individual_sprint: Raceplan,
    races_individual_sprint: List[IndividualSprintRace],
    contestants: List[dict],
    expected_startlist_individual_sprint: Startlist,
    expected_start_entries_individual_sprint: List[Startlist],
) -> None:
    """Should return an instance of Startlist equal to the expected startlist."""
    startlist, start_entries = await generate_startlist_for_individual_sprint(
        event_individual_sprint,
        competition_format_individual_sprint,
        raceclasses,
        raceplan_individual_sprint,
        races_individual_sprint,
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
    assert len(start_entries) == len(expected_start_entries_individual_sprint)
    no_of_start_entries = 0
    for start_entry in start_entries:
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
    """A competition_format object for testing."""
    return {
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_groups": "00:15:00",
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
            "ageclasses": ["J 15 år"],
            "no_of_contestants": 27,
            "ranking": True,
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
    # Add list of race_ids:
    for id in range(1, 12):
        raceplan.races.append(str(id))

    return raceplan


@pytest.fixture
async def races_individual_sprint(
    competition_format_individual_sprint: dict,
    raceplan_individual_sprint: Raceplan,
) -> List[IndividualSprintRace]:
    """Create a mock raceplan object."""
    races: List[IndividualSprintRace] = []
    races.append(
        IndividualSprintRace(
            id="1",
            order=1,
            raceclass="J15",
            round="Q",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": "REST"}},
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="2",
            order=2,
            raceclass="J15",
            round="Q",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": "REST"}},
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="3",
            order=3,
            raceclass="J15",
            round="Q",
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": "REST"}},
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="4",
            order=4,
            raceclass="J15",
            round="Q",
            index="A",
            heat=4,
            start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": "REST"}},
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="5",
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
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="6",
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
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="7",
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
            rule={"F": {"A": 4, "B": "REST"}},
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="8",
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
            rule={"F": {"A": 4, "B": "REST"}},
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="9",
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
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="10",
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
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IndividualSprintRace(
            id="11",
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
            event_id=raceplan_individual_sprint.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    assert (
        sum(race.no_of_contestants for race in races if race.round == "Q")
        == raceplan_individual_sprint.no_of_contestants
    )

    return races


@pytest.fixture
async def contestants(
    event_individual_sprint: dict, raceplan_individual_sprint: Raceplan
) -> List[dict]:
    """Create a mock contestant list object."""
    return [
        {
            "bib": 1,
            "first_name": "First",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 2,
            "first_name": "Second",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 3,
            "first_name": "Third",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 4,
            "first_name": "Fourth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 5,
            "first_name": "Fifth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 6,
            "first_name": "Sixth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 7,
            "first_name": "Seventh",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 8,
            "first_name": "Eight",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 9,
            "first_name": "Ninth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 10,
            "first_name": "Tenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 11,
            "first_name": "Eleventh",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 12,
            "first_name": "Twelfth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 13,
            "first_name": "Thirteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 14,
            "first_name": "Fourteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 15,
            "first_name": "Fifteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 16,
            "first_name": "Sixteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 17,
            "first_name": "Seventeenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 18,
            "first_name": "Eighteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 19,
            "first_name": "Nineteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 20,
            "first_name": "Twentieth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 21,
            "first_name": "Twenty First",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 22,
            "first_name": "Twenty Second",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 23,
            "first_name": "Twenty Third",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 24,
            "first_name": "Twenty Fourth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 25,
            "first_name": "Twenty Fifth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 26,
            "first_name": "Twenty Sixth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 27,
            "first_name": "Twenty Seventh",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 15 år",
            "event_id": event_individual_sprint["id"],
        },
    ]


@pytest.fixture
async def expected_startlist_individual_sprint(
    event_individual_sprint: dict, raceplan_individual_sprint: Raceplan
) -> Startlist:
    """Create a mock startlist object."""
    startlist = Startlist(
        event_id=event_individual_sprint["id"],
        no_of_contestants=raceplan_individual_sprint.no_of_contestants,
        start_entries=list(),
    )
    return startlist


@pytest.fixture
async def expected_start_entries_individual_sprint(
    event_individual_sprint: dict, raceplan_individual_sprint: Raceplan
) -> List[StartEntry]:
    """Create a mock list of start_entries object."""
    start_entries: List[StartEntry] = []
    start_entries.append(
        StartEntry(
            id="",
            race_id="1",
            startlist_id="",
            bib=1,
            starting_position=1,
            name="First Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            race_id="1",
            startlist_id="",
            bib=2,
            starting_position=2,
            name="Second Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            race_id="1",
            startlist_id="",
            bib=3,
            starting_position=3,
            name="Third Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="1",
            bib=4,
            starting_position=4,
            name="Fourth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="1",
            bib=5,
            starting_position=5,
            name="Fifth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="1",
            bib=6,
            starting_position=6,
            name="Sixth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="1",
            bib=7,
            starting_position=7,
            name="Seventh Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="2",
            bib=8,
            starting_position=1,
            name="Eigth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="2",
            bib=9,
            starting_position=2,
            name="Nineth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="2",
            bib=10,
            starting_position=3,
            name="Tenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="2",
            bib=11,
            starting_position=4,
            name="Eleventh Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="2",
            bib=12,
            starting_position=5,
            name="Twelvth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="2",
            bib=13,
            starting_position=6,
            name="Thirteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="2",
            bib=14,
            starting_position=7,
            name="Fourtheenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="3",
            bib=15,
            starting_position=1,
            name="Fifteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="3",
            bib=16,
            starting_position=2,
            name="Sixteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="3",
            bib=17,
            starting_position=3,
            name="Seventeenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="3",
            bib=18,
            starting_position=4,
            name="Eighteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="3",
            bib=19,
            starting_position=5,
            name="Nineteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="3",
            bib=20,
            starting_position=6,
            name="Twentieth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="3",
            bib=21,
            starting_position=7,
            name="Twenty First Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="4",
            bib=22,
            starting_position=1,
            name="Twenty Second Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="4",
            bib=23,
            starting_position=2,
            name="Twenty Third Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="4",
            bib=24,
            starting_position=3,
            name="Twenty Fourth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="4",
            bib=25,
            starting_position=4,
            name="Twenty Fifth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="4",
            bib=26,
            starting_position=5,
            name="Twenty Sixth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="4",
            bib=27,
            name="Twenty Seventh Contender",
            club="Lyn Ski",
            starting_position=6,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
        )
    )
    return start_entries
