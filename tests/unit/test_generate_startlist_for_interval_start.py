"""Unit test cases for the startlist_commands module."""

from datetime import datetime
from functools import reduce

import pytest

from race_service.commands.startlists_commands import (
    generate_start_entries_for_interval_start,
)
from race_service.models import IntervalStartRace, Raceplan, StartEntry, Startlist

# --- Interval Start ---


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_start_entries_for_interval_start(
    competition_format_interval_start: dict,
    raceclasses: list[dict],
    races_interval_start: list[IntervalStartRace],
    contestants: list[dict],
    expected_startlist_interval_start: Startlist,
    expected_start_entries_interval_start: list[StartEntry],
) -> None:
    """Should return an instance of Raceplan equal to the expected raceplan."""
    start_entries = await generate_start_entries_for_interval_start(
        competition_format_interval_start,
        raceclasses,
        races_interval_start,
        contestants,
    )

    assert len(start_entries) == len(expected_start_entries_interval_start)
    for start_entry in start_entries:
        assert type(start_entry) is StartEntry

    # Check that the two race lists match:
    if not reduce(
        lambda x, y: x and y,
        map(
            lambda p, q: p == q,
            start_entries,
            expected_startlist_interval_start.start_entries,
        ),
        True,
    ):
        print("Calculated startlist:")
        print(*start_entries, sep="\n")
        print("----")
        print("Expected startlist:")
        print(*expected_startlist_interval_start.start_entries, sep="\n")
        msg = "Startlist does not match expected."
        raise AssertionError(msg)


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
async def raceclasses(
    event_interval_start: dict,
) -> list[dict]:
    """Create a mock raceclasses object."""
    raceclasses: list[dict] = []
    raceclasses.append(
        {
            "name": "J15",
            "group": 1,
            "order": 1,
            "ageclasses": ["J 15 år"],
            "no_of_contestants": 2,
            "event_id": event_interval_start["id"],
            "distance": "5km",
        }
    )
    raceclasses.append(
        {
            "name": "G15",
            "group": 1,
            "order": 2,
            "ageclasses": ["G 15 år"],
            "no_of_contestants": 2,
            "event_id": event_interval_start["id"],
            "distance": "5km",
        }
    )
    raceclasses.append(
        {
            "name": "J16",
            "group": 2,
            "order": 1,
            "ageclasses": ["J 16 år"],
            "no_of_contestants": 2,
            "event_id": event_interval_start["id"],
            "distance": "5km",
        }
    )
    raceclasses.append(
        {
            "name": "G16",
            "group": 2,
            "order": 2,
            "ageclasses": ["G 16 år"],
            "no_of_contestants": 2,
            "event_id": event_interval_start["id"],
            "distance": "5km",
        }
    )
    return raceclasses


@pytest.fixture
async def raceplan_interval_start(event_interval_start: dict) -> Raceplan:
    """Create a mock raceplan object."""
    raceplan = Raceplan(event_id=event_interval_start["id"], races=[])
    raceplan.id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 8
    # Add list of race_ids:
    for race_id in range(1, 6):
        raceplan.races.append(str(race_id))
    return raceplan


@pytest.fixture
async def races_interval_start(
    competition_format_interval_start: dict,
    raceplan_interval_start: Raceplan,
) -> list[IntervalStartRace]:
    """Create a mock raceplan object."""
    races: list[IntervalStartRace] = []
    races.append(
        IntervalStartRace(
            id="1",
            raceclass="J15",
            order=1,
            start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
            no_of_contestants=2,
            max_no_of_contestants=competition_format_interval_start[
                "max_no_of_contestants_in_race"
            ],
            event_id=raceplan_interval_start.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IntervalStartRace(
            id="2",
            raceclass="G15",
            order=2,
            start_time=datetime.fromisoformat("2021-08-31 09:01:00"),
            no_of_contestants=2,
            max_no_of_contestants=competition_format_interval_start[
                "max_no_of_contestants_in_race"
            ],
            event_id=raceplan_interval_start.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IntervalStartRace(
            id="3",
            raceclass="J16",
            order=3,
            start_time=datetime.fromisoformat("2021-08-31 09:11:30"),
            no_of_contestants=2,
            max_no_of_contestants=competition_format_interval_start[
                "max_no_of_contestants_in_race"
            ],
            event_id=raceplan_interval_start.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    races.append(
        IntervalStartRace(
            id="4",
            raceclass="G16",
            order=4,
            start_time=datetime.fromisoformat("2021-08-31 09:12:30"),
            no_of_contestants=2,
            max_no_of_contestants=competition_format_interval_start[
                "max_no_of_contestants_in_race"
            ],
            event_id=raceplan_interval_start.event_id,
            raceplan_id="",
            start_entries=[],
            results={},
        )
    )
    return races


@pytest.fixture
async def contestants(
    event_interval_start: dict,
) -> list[dict]:
    """Create a mock contestant list object."""
    return [
        {
            "bib": 1,
            "first_name": "First",
            "last_name": "Contender",
            "birth_date": "1970-01-01",
            "gender": "K",
            "ageclass": "J 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event_interval_start["id"],
        },
        {
            "bib": 2,
            "first_name": "Second",
            "last_name": "Contender",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "J 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event_interval_start["id"],
        },
        {
            "bib": 3,
            "first_name": "Third",
            "last_name": "Contender",
            "birth_date": "1970-01-01",
            "gender": "K",
            "ageclass": "G 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event_interval_start["id"],
        },
        {
            "bib": 4,
            "first_name": "Fourth",
            "last_name": "Contender",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "G 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event_interval_start["id"],
        },
        {
            "bib": 5,
            "first_name": "Fifth",
            "last_name": "Contender",
            "birth_date": "1970-01-01",
            "gender": "K",
            "ageclass": "J 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event_interval_start["id"],
        },
        {
            "bib": 6,
            "first_name": "Sixth",
            "last_name": "Contender",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "J 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event_interval_start["id"],
        },
        {
            "bib": 7,
            "first_name": "Seventh",
            "last_name": "Contender",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "G 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event_interval_start["id"],
        },
        {
            "bib": 8,
            "first_name": "Eight",
            "last_name": "Contender",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "G 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event_interval_start["id"],
        },
    ]


@pytest.fixture
async def expected_startlist_interval_start(
    event_interval_start: dict, raceplan_interval_start: Raceplan
) -> Startlist:
    """Create a mock startlist object."""
    return Startlist(
        event_id=event_interval_start["id"],
        no_of_contestants=raceplan_interval_start.no_of_contestants,
        start_entries=[],
    )


@pytest.fixture
async def expected_start_entries_interval_start() -> list[StartEntry]:
    """Create a mock list of start_entries object."""
    start_entries: list[StartEntry] = []
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="1",
            bib=1,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
            name="First Contender",
            club="Lyn Ski",
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="1",
            bib=2,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:00:30"),
            name="Second Contender",
            club="Lyn Ski",
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="2",
            bib=3,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:01:00"),
            name="Third Contender",
            club="Lyn Ski",
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="2",
            bib=4,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:01:30"),
            name="Fourth Contender",
            club="Lyn Ski",
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="3",
            bib=5,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:11:30"),
            name="Fifth Contender",
            club="Lyn Ski",
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="3",
            bib=6,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:12:00"),
            name="Sixth Contender",
            club="Lyn Ski",
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="4",
            bib=7,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:12:30"),
            name="Seventh Contender",
            club="Lyn Ski",
        )
    )
    start_entries.append(
        StartEntry(
            id="",
            startlist_id="",
            race_id="4",
            bib=8,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:13:00"),
            name="Eigth Contender",
            club="Lyn Ski",
        )
    )
    return start_entries
