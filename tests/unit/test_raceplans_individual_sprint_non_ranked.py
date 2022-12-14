"""Unit test cases for the event-service module."""
import asyncio
from datetime import datetime
from typing import Any, Dict, List

import pytest

from race_service.commands.raceplans_individual_sprint import (
    calculate_raceplan_individual_sprint,
)
from race_service.models import IndividualSprintRace, Raceplan

# --- Individual Sprint ---


@pytest.fixture(scope="function")
def event_loop() -> Any:
    """Redefine the event_loop fixture to have the same scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def competition_format_individual_sprint() -> dict:
    """A competition_format object for testing."""
    return {
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_groups": "00:10:00",
        "time_between_rounds": "00:05:00",
        "time_between_heats": "00:02:30",
        "rounds_ranked_classes": ["Q", "S", "F"],
        "rounds_non_ranked_classes": ["R1", "R2"],
        "max_no_of_contestants_in_raceclass": 80,
        "max_no_of_contestants_in_race": 10,
        "datatype": "individual_sprint",
        "timezone": "Europe/Oslo",
        "race_config_non_ranked": [
            {
                "max_no_of_contestants": 8,
                "rounds": ["R1", "R2"],
                "no_of_heats": {"R1": {"A": 1}, "R2": {"A": 1}},
                "from_to": {"R1": {"A": {"R2": {"A": "ALL"}}}},
            },
            {
                "max_no_of_contestants": 16,
                "rounds": ["R1", "R2"],
                "no_of_heats": {"R1": {"A": 2}, "R2": {"A": 2}},
                "from_to": {"R1": {"A": {"R2": {"A": "ALL"}}}},
            },
            {
                "max_no_of_contestants": 24,
                "rounds": ["R1", "R2"],
                "no_of_heats": {"R1": {"A": 3}, "R2": {"A": 3}},
                "from_to": {"R1": {"A": {"R2": {"A": "ALL"}}}},
            },
            {
                "max_no_of_contestants": 32,
                "rounds": ["R1", "R2"],
                "no_of_heats": {"R1": {"A": 4}, "R2": {"A": 4}},
                "from_to": {"R1": {"A": {"R2": {"A": "ALL"}}}},
            },
            {
                "max_no_of_contestants": 40,
                "rounds": ["R1", "R2"],
                "no_of_heats": {"R1": {"A": 6}, "R2": {"A": 6}},
                "from_to": {"R1": {"A": {"R2": {"A": "ALL"}}}},
            },
            {
                "max_no_of_contestants": 48,
                "rounds": ["R1", "R2"],
                "no_of_heats": {"R1": {"A": 6}, "R2": {"A": 6}},
                "from_to": {"R1": {"A": {"R2": {"A": "ALL"}}}},
            },
            {
                "max_no_of_contestants": 56,
                "rounds": ["R1", "R2"],
                "no_of_heats": {"R1": {"A": 7}, "R2": {"A": 7}},
                "from_to": {"R1": {"A": {"R2": {"A": "ALL"}}}},
            },
            {
                "max_no_of_contestants": 80,
                "rounds": ["R1", "R2"],
                "no_of_heats": {"R1": {"A": 8}, "R2": {"A": 8}},
                "from_to": {"R1": {"A": {"R2": {"A": "ALL"}}}},
            },
        ],
        "race_config_ranked": [
            {
                "max_no_of_contestants": 8,
                "rounds": ["Q", "F"],
                "no_of_heats": {"Q": {"A": 1}, "F": {"A": 1, "B": 0, "C": 0}},
                "from_to": {
                    "Q": {"A": {"F": {"A": "ALL", "B": 0}}, "C": {"F": {"C": 0}}}
                },
            },
            {
                "max_no_of_contestants": 16,
                "rounds": ["Q", "F"],
                "no_of_heats": {"Q": {"A": 2}, "F": {"A": 1, "B": 1, "C": 0}},
                "from_to": {
                    "Q": {"A": {"F": {"A": 4, "B": "REST"}}, "C": {"F": {"C": 0}}}
                },
            },
            {
                "max_no_of_contestants": 24,
                "rounds": ["Q", "S", "F"],
                "no_of_heats": {
                    "Q": {"A": 3},
                    "S": {"A": 2, "C": 0},
                    "F": {"A": 1, "B": 1, "C": 1},
                },
                "from_to": {
                    "Q": {"A": {"S": {"A": 5, "C": 0}, "F": {"C": "REST"}}},
                    "S": {"A": {"F": {"A": 4, "B": "REST"}}, "C": {"F": {"C": 0}}},
                },
            },
            {
                "max_no_of_contestants": 32,
                "rounds": ["Q", "S", "F"],
                "no_of_heats": {
                    "Q": {"A": 4},
                    "S": {"A": 2, "C": 2},
                    "F": {"A": 1, "B": 1, "C": 1},
                },
                "from_to": {
                    "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                    "S": {"A": {"F": {"A": 4, "B": "REST"}}, "C": {"F": {"C": 4}}},
                },
            },
            {
                "max_no_of_contestants": 40,
                "rounds": ["Q", "S", "F"],
                "no_of_heats": {
                    "Q": {"A": 6},
                    "S": {"A": 4, "C": 2},
                    "F": {"A": 1, "B": 1, "C": 1},
                },
                "from_to": {
                    "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                    "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 4}}},
                },
            },
            {
                "max_no_of_contestants": 48,
                "rounds": ["Q", "S", "F"],
                "no_of_heats": {
                    "Q": {"A": 6},
                    "S": {"A": 4, "C": 4},
                    "F": {"A": 1, "B": 1, "C": 1},
                },
                "from_to": {
                    "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                    "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 2}}},
                },
            },
            {
                "max_no_of_contestants": 56,
                "rounds": ["Q", "S", "F"],
                "no_of_heats": {
                    "Q": {"A": 7},
                    "S": {"A": 4, "C": 4},
                    "F": {"A": 1, "B": 1, "C": 1},
                },
                "from_to": {
                    "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                    "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 2}}},
                },
            },
            {
                "max_no_of_contestants": 80,
                "rounds": ["Q", "S", "F"],
                "no_of_heats": {
                    "Q": {"A": 8},
                    "S": {"A": 4, "C": 4},
                    "F": {"A": 1, "B": 1, "C": 1},
                },
                "from_to": {
                    "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                    "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 2}}},
                },
            },
        ],
    }


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
async def raceclasses_individual_sprint_10_contestants() -> List[Dict[str, Any]]:
    """A raceclass object for testing - 10 contestants."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G11",
            "ageclasses": ["G 11 år"],
            "event_id": "e90e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 10,
            "group": 1,
            "order": 1,
            "ranking": False,
        },
    ]


@pytest.fixture(scope="function")
async def raceclasses_individual_sprint_17_contestants() -> List[Dict[str, Any]]:
    """A raceclass object for testing - 17 contestants."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J11",
            "ageclasses": ["J 11 år"],
            "event_id": "e90e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 17,
            "group": 1,
            "order": 1,
            "ranking": False,
        },
    ]


@pytest.fixture(scope="function")
async def raceclasses_individual_sprint_27_contestants() -> List[Dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclasses": ["J 15 år"],
            "event_id": "e90e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 27,
            "group": 1,
            "order": 1,
            "ranking": False,
        },
    ]


@pytest.fixture(scope="function")
async def expected_raceplan_individual_sprint_10_contestants(
    event_individual_sprint: dict,
) -> Raceplan:
    """Create a mock raceplan object - 10 contestants."""
    raceplan = Raceplan(event_id=event_individual_sprint["id"], races=list())
    raceplan.id = "190e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 10

    return raceplan


@pytest.fixture(scope="function")
async def expected_raceplan_individual_sprint_17_contestants(
    event_individual_sprint: dict,
) -> Raceplan:
    """Create a mock raceplan object - 17 contestants."""
    raceplan = Raceplan(event_id=event_individual_sprint["id"], races=list())
    raceplan.id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 17

    return raceplan


@pytest.fixture(scope="function")
async def expected_raceplan_individual_sprint_27_contestants(
    event_individual_sprint: dict,
) -> Raceplan:
    """Create a mock raceplan object - 27 contestants."""
    raceplan = Raceplan(event_id=event_individual_sprint["id"], races=list())
    raceplan.id = "390e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 27

    return raceplan


@pytest.fixture(scope="function")
async def expected_races_individual_sprint_10_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
) -> List[IndividualSprintRace]:
    """Create a mock raceplan object, races - 10 contestants."""
    races: List[IndividualSprintRace] = []
    races.append(
        IndividualSprintRace(
            id="",
            order=1,
            raceclass="G11",
            round="R1",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=5,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            raceclass="G11",
            round="R1",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=5,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            raceclass="G11",
            round="R2",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
            no_of_contestants=5,
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
            order=4,
            raceclass="G11",
            round="R2",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:10:00"),
            no_of_contestants=5,
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


@pytest.fixture(scope="function")
async def expected_races_individual_sprint_17_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
) -> List[IndividualSprintRace]:
    """Create a mock raceplan object, races - 17 contestants."""
    races: List[IndividualSprintRace] = []
    races.append(
        IndividualSprintRace(
            id="",
            order=1,
            raceclass="J11",
            round="R1",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            raceclass="J11",
            round="R1",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            raceclass="J11",
            round="R1",
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
            no_of_contestants=5,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            raceclass="J11",
            round="R2",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:10:00"),
            no_of_contestants=6,
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
            order=5,
            raceclass="J11",
            round="R2",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:12:30"),
            no_of_contestants=6,
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
            order=6,
            raceclass="J11",
            round="R2",
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:15:00"),
            no_of_contestants=5,
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


@pytest.fixture(scope="function")
async def expected_races_individual_sprint_27_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
) -> List[IndividualSprintRace]:
    """Create a mock raceplan object, races - 27 contestants."""
    races: List[IndividualSprintRace] = []
    races.append(
        IndividualSprintRace(
            id="",
            order=1,
            raceclass="J15",
            round="R1",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            round="R1",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            round="R1",
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            round="R1",
            index="A",
            heat=4,
            start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"R2": {"A": "ALL"}},
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
            round="R2",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:12:30"),
            no_of_contestants=7,
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
            order=6,
            raceclass="J15",
            round="R2",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:15:00"),
            no_of_contestants=7,
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
            order=7,
            raceclass="J15",
            round="R2",
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
            no_of_contestants=7,
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
            order=8,
            raceclass="J15",
            round="R2",
            index="A",
            heat=4,
            start_time=datetime.fromisoformat("2021-09-29 09:20:00"),
            no_of_contestants=6,
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
async def test_calculate_raceplan_individual_sprint_non_ranked_10_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
    raceclasses_individual_sprint_10_contestants: List[dict],
    expected_raceplan_individual_sprint_10_contestants: Raceplan,
    expected_races_individual_sprint_10_contestants: List[IndividualSprintRace],
) -> None:
    """Should return a tuple of Raceplan and races equal to the expected raceplan."""
    raceplan, races = await calculate_raceplan_individual_sprint(
        event_individual_sprint,
        competition_format_individual_sprint,
        raceclasses_individual_sprint_10_contestants,
    )

    assert type(raceplan) is Raceplan
    assert raceplan.id is None
    assert (
        raceplan.event_id == expected_raceplan_individual_sprint_10_contestants.event_id
    )
    # Check that no_of_contestants corresponds to the number given in raceclasses:
    assert (
        raceplan.no_of_contestants
        == expected_raceplan_individual_sprint_10_contestants.no_of_contestants
    )
    # Check that all the contestants have been given a round 1:
    assert (
        sum(race.no_of_contestants for race in races if race.round == "R1")
        == raceplan.no_of_contestants
    )

    # Check that the sum number of contestants are the same in round 1:
    assert sum(race.no_of_contestants for race in races if race.round == "R1") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_10_contestants
        if race.round == "R1"
    ), "wrong sum no_of_contestants in round R1"

    # Check that the sum number of contestants are the same in round 2:
    assert sum(race.no_of_contestants for race in races if race.round == "R2") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_10_contestants
        if race.round == "R2"
    ), "wrong sum no_of_contestants in round R2"

    # Check that there are correct number of races:
    assert len(raceplan.races) == 0
    assert len(races) == len(expected_races_individual_sprint_10_contestants)

    # Check that the two race lists match:
    print("Calculated raceplan:")
    i = 0
    for race in races:
        print(f"[{i}]: {race}", sep="\n")
        i += 1

    print("----")
    print("Expected raceplan:")
    i = 0
    for race in expected_races_individual_sprint_10_contestants:
        print(f"[{i}]: {race}", sep="\n")
        i += 1

    i = 0
    for race in races:
        assert (
            race == expected_races_individual_sprint_10_contestants[i]
        ), f"race with index {i} did not match"
        i += 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_raceplan_individual_sprint_non_ranked_27_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
    raceclasses_individual_sprint_27_contestants: List[dict],
    expected_raceplan_individual_sprint_27_contestants: Raceplan,
    expected_races_individual_sprint_27_contestants: List[IndividualSprintRace],
) -> None:
    """Should return a tuple of Raceplan and races equal to the expected raceplan."""
    raceplan, races = await calculate_raceplan_individual_sprint(
        event_individual_sprint,
        competition_format_individual_sprint,
        raceclasses_individual_sprint_27_contestants,
    )

    assert type(raceplan) is Raceplan
    assert raceplan.id is None
    assert (
        raceplan.event_id == expected_raceplan_individual_sprint_27_contestants.event_id
    )
    # Check that no_of_contestants corresponds to the number given in raceclasses:
    assert (
        raceplan.no_of_contestants
        == expected_raceplan_individual_sprint_27_contestants.no_of_contestants
    )
    # Check that all the contestants have been given a round 1:
    assert (
        sum(race.no_of_contestants for race in races if race.round == "R1")
        == raceplan.no_of_contestants
    )

    # Check that the sum number of contestants are the same in round R1:
    assert sum(race.no_of_contestants for race in races if race.round == "R1") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_27_contestants
        if race.round == "R1"
    ), "wrong sum no_of_contestants in round 1"

    # Check that the sum number of contestants are the same in round R2:
    assert sum(race.no_of_contestants for race in races if race.round == "R2") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_27_contestants
        if race.round == "R2"
    ), "wrong sum no_of_contestants in round R2"

    # Check that there are correct number of races:
    assert len(raceplan.races) == 0
    assert len(races) == len(expected_races_individual_sprint_27_contestants)

    # Check that the two race lists match:
    print("Calculated raceplan:")
    i = 0
    for race in races:
        print(f"[{i}]: {race}", sep="\n")
        i += 1

    print("----")
    print("Expected raceplan:")
    i = 0
    for race in expected_races_individual_sprint_27_contestants:
        print(f"[{i}]: {race}", sep="\n")
        i += 1

    i = 0
    for race in races:
        assert (
            race == expected_races_individual_sprint_27_contestants[i]
        ), f"race with index {i} did not match"
        i += 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_raceplan_individual_sprint_non_ranked_17_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
    raceclasses_individual_sprint_17_contestants: List[dict],
    expected_raceplan_individual_sprint_17_contestants: Raceplan,
    expected_races_individual_sprint_17_contestants: List[IndividualSprintRace],
) -> None:
    """Should return a tuple of Raceplan and races equal to the expected raceplan."""
    raceplan, races = await calculate_raceplan_individual_sprint(
        event_individual_sprint,
        competition_format_individual_sprint,
        raceclasses_individual_sprint_17_contestants,
    )

    assert type(raceplan) is Raceplan
    assert raceplan.id is None
    assert (
        raceplan.event_id == expected_raceplan_individual_sprint_17_contestants.event_id
    )
    # Check that no_of_contestants corresponds to the number given in raceclasses:
    assert (
        raceplan.no_of_contestants
        == expected_raceplan_individual_sprint_17_contestants.no_of_contestants
    )
    # Check that all the contestants have been given a round 1:
    assert (
        sum(race.no_of_contestants for race in races if race.round == "R1")
        == raceplan.no_of_contestants
    )

    # Check that the sum number of contestants are the same in round R1:
    assert sum(race.no_of_contestants for race in races if race.round == "R1") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_17_contestants
        if race.round == "R1"
    ), "wrong sum no_of_contestants in round R2"

    # Check that the sum number of contestants are the same in round R2:
    assert sum(race.no_of_contestants for race in races if race.round == "R2") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_17_contestants
        if race.round == "R2"
    ), "wrong sum no_of_contestants in round R2"

    # Check that there are correct number of races:
    assert len(raceplan.races) == 0
    assert len(races) == len(expected_races_individual_sprint_17_contestants)

    # Check that the two race lists match:
    print("Calculated raceplan:")
    i = 0
    for race in races:
        print(f"[{i}]: {race}", sep="\n")
        i += 1

    print("----")
    print("Expected raceplan:")
    i = 0
    for race in expected_races_individual_sprint_17_contestants:
        print(f"[{i}]: {race}", sep="\n")
        i += 1

    i = 0
    for race in races:
        assert (
            race == expected_races_individual_sprint_17_contestants[i]
        ), f"race with index {i} did not match"
        i += 1


# helpers
def print_races(races: List[IndividualSprintRace]) -> None:
    """Print races in given round."""
    print("--- races ---")
    for race in races:
        print(f"{race.order}: {race}\n")
