"""Unit test cases for the startlist_commands module."""
from datetime import datetime
from functools import reduce
from typing import List

import pytest

from race_service.commands.startlists_commands import (
    generate_startlist_for_interval_start,
)
from race_service.models import IntervalStartRace, Raceplan, StartEvent, Startlist

# --- Interval Start ---


@pytest.fixture
async def competition_format_interval_start() -> dict:
    """An competition_format object for testing."""
    return {
        "name": "Interval Start",
        "starting_order": "Draw",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
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
async def raceclasses(
    event_interval_start: dict, contestants: List[dict]
) -> List[dict]:
    """Create a mock raceclasses object."""
    raceclasses: List[dict] = []
    raceclasses.append(
        {
            "name": "J15",
            "group": 1,
            "order": 1,
            "ageclass_name": "J 15 år",
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
            "ageclass_name": "G 15 år",
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
            "ageclass_name": "J 16 år",
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
            "ageclass_name": "G 16 år",
            "no_of_contestants": 2,
            "event_id": event_interval_start["id"],
            "distance": "5km",
        }
    )
    return raceclasses


@pytest.fixture
async def raceplan_interval_start(event_interval_start: dict) -> Raceplan:
    """Create a mock raceplan object."""
    raceplan = Raceplan(event_id=event_interval_start["id"], races=list())
    raceplan.id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 8
    raceplan.races.append(
        IntervalStartRace(
            id="1",
            raceclass="J15",
            order=1,
            start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
            no_of_contestants=2,
        )
    )
    raceplan.races.append(
        IntervalStartRace(
            id="2",
            raceclass="G15",
            order=2,
            start_time=datetime.fromisoformat("2021-08-31 09:01:00"),
            no_of_contestants=2,
        )
    )
    raceplan.races.append(
        IntervalStartRace(
            id="3",
            raceclass="J16",
            order=3,
            start_time=datetime.fromisoformat("2021-08-31 09:11:30"),
            no_of_contestants=2,
        )
    )
    raceplan.races.append(
        IntervalStartRace(
            id="4",
            raceclass="G16",
            order=4,
            start_time=datetime.fromisoformat("2021-08-31 09:12:30"),
            no_of_contestants=2,
        )
    )
    return raceplan


@pytest.fixture
async def contestants(
    event_interval_start: dict, raceplan_interval_start: Raceplan
) -> List[dict]:
    """Create a mock contestant list object."""
    return [
        {
            "bib": 1,
            "first_name": "Cont E.",
            "last_name": "Stant",
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
            "first_name": "Conte E.",
            "last_name": "Stante",
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
            "first_name": "Conta E.",
            "last_name": "Stanta",
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
            "first_name": "Conti E.",
            "last_name": "Stanti",
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
            "first_name": "AContA E.",
            "last_name": "AStanta",
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
            "first_name": "AConte E.",
            "last_name": "AStante",
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
            "first_name": "Contas E.",
            "last_name": "Stantas",
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
            "first_name": "Contus E.",
            "last_name": "Stantus",
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
    """Create a mock raceplan object."""
    startlist = Startlist(
        event_id=event_interval_start["id"],
        no_of_contestants=raceplan_interval_start.no_of_contestants,
        start_events=list(),
    )
    startlist.start_events.append(
        StartEvent(
            id="",
            race_id="1",
            bib=1,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
        )
    )
    startlist.start_events.append(
        StartEvent(
            id="",
            race_id="1",
            bib=2,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:00:30"),
        )
    )
    startlist.start_events.append(
        StartEvent(
            id="",
            race_id="2",
            bib=3,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:01:00"),
        )
    )
    startlist.start_events.append(
        StartEvent(
            id="",
            race_id="2",
            bib=4,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:01:30"),
        )
    )
    startlist.start_events.append(
        StartEvent(
            id="",
            race_id="3",
            bib=5,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:11:30"),
        )
    )
    startlist.start_events.append(
        StartEvent(
            id="",
            race_id="3",
            bib=6,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:12:00"),
        )
    )
    startlist.start_events.append(
        StartEvent(
            id="",
            race_id="4",
            bib=7,
            starting_position=1,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:12:30"),
        )
    )
    startlist.start_events.append(
        StartEvent(
            id="",
            race_id="4",
            bib=8,
            starting_position=2,
            scheduled_start_time=datetime.fromisoformat("2021-08-31 09:13:00"),
        )
    )
    return startlist


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_startlist_for_interval_start(
    event_interval_start: dict,
    competition_format_interval_start: dict,
    raceclasses: List[dict],
    raceplan_interval_start: Raceplan,
    contestants: List[dict],
    expected_startlist_interval_start: Startlist,
) -> None:
    """Should return an instance of Raceplan equal to the expected raceplan."""
    startlist = await generate_startlist_for_interval_start(
        event_interval_start,
        competition_format_interval_start,
        raceclasses,
        raceplan_interval_start,
        contestants,
    )

    assert type(startlist) is Startlist
    assert startlist.id is None
    assert startlist.event_id == expected_startlist_interval_start.event_id
    assert (
        startlist.no_of_contestants
        == expected_startlist_interval_start.no_of_contestants
    )
    assert startlist.no_of_contestants == sum(
        rc["no_of_contestants"] for rc in raceclasses
    )
    assert len(startlist.start_events) == len(
        expected_startlist_interval_start.start_events
    )
    no_of_start_events = 0
    for start_event in startlist.start_events:
        assert type(start_event) is StartEvent
        no_of_start_events += 1
    assert no_of_start_events == startlist.no_of_contestants

    # Check that the two race lists match:
    if not reduce(
        lambda x, y: x and y,
        map(
            lambda p, q: p == q,
            startlist.start_events,
            expected_startlist_interval_start.start_events,
        ),
        True,
    ):
        print("Calculated startlist:")
        print(*startlist.start_events, sep="\n")
        print("----")
        print("Expected startlist:")
        print(*expected_startlist_interval_start.start_events, sep="\n")
        raise AssertionError("Startlist does not match expected.")
    else:
        assert 1 == 1
