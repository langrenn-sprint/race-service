"""Unit test cases for the startlist_commands module."""

from datetime import datetime
from functools import reduce

import pytest

from race_service.commands.startlists_commands import (
    generate_start_entries_for_individual_sprint,
)
from race_service.models import IndividualSprintRace, Raceplan, StartEntry, Startlist

# --- Individual Sprint, not ranked. ---


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_startlist_for_individual_sprint_not_ranked(
    competition_format_individual_sprint: dict,
    raceclasses: list[dict],
    races_individual_sprint: list[IndividualSprintRace],
    contestants: list[dict],
    expected_startlist_individual_sprint: Startlist,
    expected_start_entries_individual_sprint: list[Startlist],
) -> None:
    """Should return an instance of Startlist equal to the expected startlist."""
    start_entries = await generate_start_entries_for_individual_sprint(
        competition_format_individual_sprint,
        raceclasses,
        races_individual_sprint,
        contestants,
    )

    assert len(start_entries) == len(expected_start_entries_individual_sprint)
    for start_entry in start_entries:
        assert type(start_entry) is StartEntry

    # Check that the two race lists match:
    if not reduce(
        lambda x, y: x and y,
        map(
            lambda p, q: p == q,
            start_entries,
            expected_startlist_individual_sprint.start_entries,
        ),
        True,
    ):
        print("Calculated startlist:")
        print(*start_entries, sep="\n")
        print("----")
        print("Expected startlist:")
        print(*expected_startlist_individual_sprint.start_entries, sep="\n")
        msg = "Startlist does not match expected."
        raise AssertionError(msg)


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
        "rounds_ranked_classes": ["Q", "S", "F"],
        "rounds_non_ranked_classes": ["R1", "R2"],
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
    event_individual_sprint: dict, contestants: list[dict]
) -> list[dict]:
    """Create a mock raceclasses object."""
    raceclasses: list[dict] = []
    raceclasses.append(
        {
            "name": "J10",
            "group": 1,
            "order": 1,
            "ageclasses": ["J 10 år"],
            "no_of_contestants": 27,
            "ranking": False,
            "event_id": event_individual_sprint["id"],
            "distance": "5km",
        }
    )
    return raceclasses


@pytest.fixture
async def raceplan_individual_sprint(event_individual_sprint: dict) -> Raceplan:
    """Create a mock raceplan object."""
    raceplan = Raceplan(event_id=event_individual_sprint["id"], races=[])
    raceplan.id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 27
    # Add list of race_ids:
    for race_id in range(1, 9):
        raceplan.races.append(str(race_id))

    return raceplan


@pytest.fixture
async def races_individual_sprint(
    competition_format_individual_sprint: dict,
    raceplan_individual_sprint: Raceplan,
) -> list[IndividualSprintRace]:
    """Create a mock raceplan object."""
    races: list[IndividualSprintRace] = []
    races.append(
        IndividualSprintRace(
            id="1",
            order=1,
            raceclass="J10",
            round="R1",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            raceclass="J10",
            round="R1",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            raceclass="J10",
            round="R1",
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            raceclass="J10",
            round="R1",
            index="A",
            heat=4,
            start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            raceclass="J10",
            round="R2",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
            no_of_contestants=7,
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
            id="6",
            order=6,
            raceclass="J10",
            round="R2",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
            no_of_contestants=7,
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
            id="7",
            order=7,
            raceclass="J10",
            round="R2",
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
            no_of_contestants=7,
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
            id="8",
            order=8,
            raceclass="J10",
            round="R2",
            index="A",
            heat=4,
            start_time=datetime.fromisoformat("2021-09-29 09:25:00"),
            no_of_contestants=6,
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
    return races


@pytest.fixture
async def contestants(
    event_individual_sprint: dict, raceplan_individual_sprint: Raceplan
) -> list[dict]:
    """Create a mock contestant list object."""
    return [
        {
            "bib": 1,
            "first_name": "First",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 2,
            "first_name": "Second",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 3,
            "first_name": "Third",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 4,
            "first_name": "Fourth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 5,
            "first_name": "Fifth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 6,
            "first_name": "Sixth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 7,
            "first_name": "Seventh",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 8,
            "first_name": "Eight",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 9,
            "first_name": "Ninth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 10,
            "first_name": "Tenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 11,
            "first_name": "Eleventh",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 12,
            "first_name": "Twelfth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 13,
            "first_name": "Thirteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 14,
            "first_name": "Fourteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 15,
            "first_name": "Fifteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 16,
            "first_name": "Sixteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 17,
            "first_name": "Seventeenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 18,
            "first_name": "Eighteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 19,
            "first_name": "Nineteenth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 20,
            "first_name": "Twentieth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 21,
            "first_name": "Twenty First",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 22,
            "first_name": "Twenty Second",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 23,
            "first_name": "Twenty Third",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 24,
            "first_name": "Twenty Fourth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 25,
            "first_name": "Twenty Fifth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 26,
            "first_name": "Twenty Sixth",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
        {
            "bib": 27,
            "first_name": "Twenty Seventh",
            "last_name": "Contender",
            "club": "Lyn Ski",
            "ageclass": "J 10 år",
            "event_id": event_individual_sprint["id"],
        },
    ]


@pytest.fixture
async def expected_startlist_individual_sprint(
    event_individual_sprint: dict, raceplan_individual_sprint: Raceplan
) -> Startlist:
    """Create a mock startlist object."""
    return Startlist(
        event_id=event_individual_sprint["id"],
        no_of_contestants=raceplan_individual_sprint.no_of_contestants,
        start_entries=[],
    )


@pytest.fixture
async def expected_start_entries_individual_sprint() -> list[StartEntry]:
    """Create a mock list of start_entries object."""
    start_entries: list[StartEntry] = []
    # R1:
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
    # R2:
    start_entries.append(
        StartEntry(
            id="",
            race_id="5",
            startlist_id="",
            bib=1,
            starting_position=1,
            name="First Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            race_id="5",
            startlist_id="",
            bib=2,
            starting_position=2,
            name="Second Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            race_id="5",
            startlist_id="",
            bib=3,
            starting_position=3,
            name="Third Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="5",
            bib=4,
            starting_position=4,
            name="Fourth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="5",
            bib=5,
            starting_position=5,
            name="Fifth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="5",
            bib=6,
            starting_position=6,
            name="Sixth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="5",
            bib=7,
            starting_position=7,
            name="Seventh Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="6",
            bib=8,
            starting_position=1,
            name="Eigth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="6",
            bib=9,
            starting_position=2,
            name="Nineth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="6",
            bib=10,
            starting_position=3,
            name="Tenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="6",
            bib=11,
            starting_position=4,
            name="Eleventh Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="6",
            bib=12,
            starting_position=5,
            name="Twelvth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="6",
            bib=13,
            starting_position=6,
            name="Thirteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="6",
            bib=14,
            starting_position=7,
            name="Fourtheenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="7",
            bib=15,
            starting_position=1,
            name="Fifteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="7",
            bib=16,
            starting_position=2,
            name="Sixteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="7",
            bib=17,
            starting_position=3,
            name="Seventeenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="7",
            bib=18,
            starting_position=4,
            name="Eighteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="7",
            bib=19,
            starting_position=5,
            name="Nineteenth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="7",
            bib=20,
            starting_position=6,
            name="Twentieth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="7",
            bib=21,
            starting_position=7,
            name="Twenty First Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:22:30"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="8",
            bib=22,
            starting_position=1,
            name="Twenty Second Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:25:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="8",
            bib=23,
            starting_position=2,
            name="Twenty Third Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:25:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="8",
            bib=24,
            starting_position=3,
            name="Twenty Fourth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:25:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="8",
            bib=25,
            starting_position=4,
            name="Twenty Fifth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:25:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="8",
            bib=26,
            starting_position=5,
            name="Twenty Sixth Contender",
            club="Lyn Ski",
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:25:00"),
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="8",
            bib=27,
            name="Twenty Seventh Contender",
            club="Lyn Ski",
            starting_position=6,
            scheduled_start_time=datetime.fromisoformat("2021-09-29 09:25:00"),
        )
    )
    return start_entries
