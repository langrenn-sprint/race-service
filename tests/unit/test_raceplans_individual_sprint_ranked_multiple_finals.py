"""Unit test cases for the event-service module."""

from datetime import datetime
from typing import Any

import pytest

from race_service.commands.raceplans_individual_sprint import (
    calculate_raceplan_individual_sprint,
)
from race_service.models import IndividualSprintRace, Raceplan

# --- Individual Sprint ---


@pytest.fixture
async def race_config() -> list[dict[str, Any]]:
    """A race_config used in competition_format."""
    return [
        {
            "max_no_of_contestants": 8,
            "rounds": ["Q", "S", "F"],
            "no_of_heats": {
                "Q": {"A": 3},
                "S": {"A": 2, "C": 0},
                "F": {"A": 1, "B1": 1, "B2": 1, "C": 1},
            },
            "from_to": {
                "Q": {"A": {"S": {"A": 5, "C": 0}}},
                "S": {
                    "A": {"F": {"A": 4, "B1": 2, "B2": "REST"}},
                    "C": {"F": {"C": 0}},
                },
            },
        },
        {
            "max_no_of_contestants": 80,
            "rounds": ["Q", "S", "F"],
            "no_of_heats": {
                "Q": {"A": 3},
                "S": {"A": 2, "C": 0},
                "F": {"A": 1, "B1": 1, "B2": 1, "C": 1},
            },
            "from_to": {
                "Q": {"A": {"S": {"A": 5, "C": 0}}},
                "S": {
                    "A": {"F": {"A": 4, "B1": 2, "B2": "REST"}},
                    "C": {"F": {"C": 0}},
                },
            },
        },
    ]


@pytest.fixture
async def competition_format_individual_sprint(
    race_config: list[dict[str, Any]],
) -> dict:
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
        "race_config_ranked": race_config,
        "race_config_non_ranked": None,
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
async def raceclasses_individual_sprint_10_contestants() -> list[dict[str, Any]]:
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
            "ranking": True,
        },
    ]


@pytest.fixture
async def raceclasses_individual_sprint_17_contestants() -> list[dict[str, Any]]:
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
            "ranking": True,
        },
    ]


@pytest.fixture
async def raceclasses_individual_sprint_27_contestants() -> list[dict[str, Any]]:
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
            "ranking": True,
        },
    ]


@pytest.fixture
async def expected_raceplan_individual_sprint_10_contestants(
    event_individual_sprint: dict,
) -> Raceplan:
    """Create a mock raceplan object - 10 contestants."""
    raceplan = Raceplan(event_id=event_individual_sprint["id"], races=[])
    raceplan.id = "190e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 10

    return raceplan


@pytest.fixture
async def expected_raceplan_individual_sprint_17_contestants(
    event_individual_sprint: dict,
) -> Raceplan:
    """Create a mock raceplan object - 17 contestants."""
    raceplan = Raceplan(event_id=event_individual_sprint["id"], races=[])
    raceplan.id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 17

    return raceplan


@pytest.fixture
async def expected_raceplan_individual_sprint_27_contestants(
    event_individual_sprint: dict,
) -> Raceplan:
    """Create a mock raceplan object - 27 contestants."""
    raceplan = Raceplan(event_id=event_individual_sprint["id"], races=[])
    raceplan.id = "390e70d5-0933-4af0-bb53-1d705ba7eb95"
    raceplan.no_of_contestants = 27

    return raceplan


@pytest.fixture
async def expected_races_individual_sprint_10_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
) -> list[IndividualSprintRace]:
    """Create a mock raceplan object, races - 10 contestants."""
    races: list[IndividualSprintRace] = []
    races.append(
        IndividualSprintRace(
            id="",
            order=1,
            raceclass="G11",
            round="Q",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=5,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"F": {"A": 4, "B": "REST"}},
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
            round="Q",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=5,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"F": {"A": 4, "B": "REST"}},
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
            round="F",
            index="B",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:12:30"),
            no_of_contestants=2,
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
            round="F",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:15:00"),
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


@pytest.fixture
async def expected_races_individual_sprint_17_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
) -> list[IndividualSprintRace]:
    """Create a mock raceplan object, races - 17 contestants."""
    races: list[IndividualSprintRace] = []
    races.append(
        IndividualSprintRace(
            id="",
            order=1,
            raceclass="J11",
            round="Q",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:00:00"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
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
            round="Q",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
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
            round="Q",
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
            no_of_contestants=5,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
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
            round="S",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:15:00"),
            no_of_contestants=8,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"F": {"A": 4, "B": "REST"}},
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
            round="S",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:17:30"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"F": {"A": 4, "B": "REST"}},
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
            round="F",
            index="C",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:27:30"),
            no_of_contestants=2,
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
            raceclass="J11",
            round="F",
            index="B",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:30:00"),
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
            raceclass="J11",
            round="F",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-09-29 09:32:30"),
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


@pytest.fixture
async def expected_races_individual_sprint_27_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
) -> list[IndividualSprintRace]:
    """Create a mock raceplan object, races - 27 contestants."""
    races: list[IndividualSprintRace] = []
    races.append(
        IndividualSprintRace(
            id="",
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
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-09-29 09:02:30"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": "REST"}},
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
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-09-29 09:05:00"),
            no_of_contestants=7,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": "REST"}},
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
            index="A",
            heat=4,
            start_time=datetime.fromisoformat("2021-09-29 09:07:30"),
            no_of_contestants=6,
            max_no_of_contestants=competition_format_individual_sprint[
                "max_no_of_contestants_in_race"
            ],
            rule={"S": {"A": 4, "C": "REST"}},
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
            rule={"F": {"A": 4, "B": "REST"}},
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
            rule={"F": {"A": 4, "B": "REST"}},
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


@pytest.mark.skip("Test not fully implemented.")
@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_raceplan_individual_sprint_10_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
    raceclasses_individual_sprint_10_contestants: list[dict],
    expected_raceplan_individual_sprint_10_contestants: Raceplan,
    expected_races_individual_sprint_10_contestants: list[IndividualSprintRace],
) -> None:
    """Should return a tuple of Raceplan and races equal to the expected raceplan."""
    raceplan, races = await calculate_raceplan_individual_sprint(
        event_individual_sprint,
        competition_format_individual_sprint,
        raceclasses_individual_sprint_10_contestants,
    )
    await _print_raceplan(raceplan, races)

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
    # Check that all the contestants have been given a Quarterfinal:
    assert (
        sum(race.no_of_contestants for race in races if race.round == "Q")
        == raceplan.no_of_contestants
    )

    # Check that the sum number of contestants are the same in round Q:
    assert sum(race.no_of_contestants for race in races if race.round == "Q") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_10_contestants
        if race.round == "Q"
    ), "wrong sum no_of_contestants in round Q"

    # Check that the sum number of contestants are the same in round S:
    assert sum(race.no_of_contestants for race in races if race.round == "S") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_10_contestants
        if race.round == "S"
    ), "wrong sum no_of_contestants in round S"

    # Check that the sum number of contestants are the same in round F:
    print_races(races)
    assert sum(race.no_of_contestants for race in races if race.round == "F") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_10_contestants
        if race.round == "F"
    ), "wrong sum no_of_contestants in round F"

    # Check that there are correct number of races:
    assert len(raceplan.races) == 0
    assert len(races) == len(expected_races_individual_sprint_10_contestants)

    # Check that the two race lists match:
    print("Calculated raceplan:")
    for i, race in enumerate(races):
        print(f"[{i}]: {race}")

    print("----")
    print("Expected raceplan:")
    for i, race in enumerate(expected_races_individual_sprint_10_contestants):
        print(f"[{i}]: {race}")

    for i, race in enumerate(races):
        assert race == expected_races_individual_sprint_10_contestants[i], (
            f"race with index {i} did not match"
        )


@pytest.mark.skip("Test not fully implemented.")
@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_raceplan_individual_sprint_27_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
    raceclasses_individual_sprint_27_contestants: list[dict],
    expected_raceplan_individual_sprint_27_contestants: Raceplan,
    expected_races_individual_sprint_27_contestants: list[IndividualSprintRace],
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
    # Check that all the contestants have been given a Quarterfinal:
    assert (
        sum(race.no_of_contestants for race in races if race.round == "Q")
        == raceplan.no_of_contestants
    )

    # Check that the sum number of contestants are the same in round Q:
    assert sum(race.no_of_contestants for race in races if race.round == "Q") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_27_contestants
        if race.round == "Q"
    ), "wrong sum no_of_contestants in round Q"

    # Check that the sum number of contestants are the same in round S:
    assert sum(race.no_of_contestants for race in races if race.round == "S") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_27_contestants
        if race.round == "S"
    ), "wrong sum no_of_contestants in round S"

    # Check that the sum number of contestants are the same in round F:
    assert sum(race.no_of_contestants for race in races if race.round == "F") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_27_contestants
        if race.round == "F"
    ), "wrong sum no_of_contestants in round F"

    # Check that there are correct number of races:
    assert len(raceplan.races) == 0
    assert len(races) == len(expected_races_individual_sprint_27_contestants)

    # Check that the two race lists match:
    print("Calculated raceplan:")
    for i, race in enumerate(races):
        print(f"[{i}]: {race}")

    print("----")
    print("Expected raceplan:")
    for i, race in enumerate(expected_races_individual_sprint_27_contestants):
        print(f"[{i}]: {race}")

    for i, race in enumerate(races):
        assert race == expected_races_individual_sprint_27_contestants[i], (
            f"race with index {i} did not match"
        )


@pytest.mark.skip("Test not fully implemented.")
@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_raceplan_individual_sprint_17_contestants(
    competition_format_individual_sprint: dict,
    event_individual_sprint: dict,
    raceclasses_individual_sprint_17_contestants: list[dict],
    expected_raceplan_individual_sprint_17_contestants: Raceplan,
    expected_races_individual_sprint_17_contestants: list[IndividualSprintRace],
) -> None:
    """Should return a tuple of Raceplan and races equal to the expected raceplan."""
    raceplan, races = await calculate_raceplan_individual_sprint(
        event_individual_sprint,
        competition_format_individual_sprint,
        raceclasses_individual_sprint_17_contestants,
    )

    await _print_raceplan(raceplan, races)

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
    # Check that all the contestants have been given a Quarterfinal:
    assert (
        sum(race.no_of_contestants for race in races if race.round == "Q")
        == raceplan.no_of_contestants
    )

    # Check that the sum number of contestants are the same in round Q:
    assert sum(race.no_of_contestants for race in races if race.round == "Q") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_17_contestants
        if race.round == "Q"
    ), "wrong sum no_of_contestants in round Q"

    # Check that the sum number of contestants are the same in round S:
    assert sum(race.no_of_contestants for race in races if race.round == "S") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_17_contestants
        if race.round == "S"
    ), "wrong sum no_of_contestants in round S"

    # Check that the sum number of contestants are the same in round F:
    assert sum(race.no_of_contestants for race in races if race.round == "F") == sum(
        race.no_of_contestants
        for race in expected_races_individual_sprint_17_contestants
        if race.round == "F"
    ), "wrong sum no_of_contestants in round F"

    # Check that there are correct number of races:
    assert len(raceplan.races) == 0
    assert len(races) == len(expected_races_individual_sprint_17_contestants)

    # Check that the two race lists match:
    print("Calculated raceplan:")
    for i, race in enumerate(races):
        print(f"[{i}]: {race}")

    print("----")
    print("Expected raceplan:")
    for i, race in enumerate(expected_races_individual_sprint_17_contestants):
        print(f"[{i}]: {race}")

    for i, race in enumerate(races):
        assert race == expected_races_individual_sprint_17_contestants[i], (
            f"race with index {i} did not match"
        )


# helpers
def print_races(races: list[IndividualSprintRace]) -> None:
    """Print races in given round."""
    print("--- races ---")
    for race in races:
        print(f"{race.order}: {race}\n")


async def _print_raceplan(
    raceplan: Raceplan, races: list[IndividualSprintRace]
) -> None:
    print(f"event_id: {raceplan.event_id}")
    print(f"no_of_contestants: {raceplan.no_of_contestants}")
    print("order;start_time;raceclass;round;index;heat;no_of_contestants;rule")
    for race in races:
        print(
            str(race.order)
            + ";"
            + str(race.start_time)
            + ";"
            + str(race.raceclass)
            + ";"
            + str(race.round)
            + ";"
            + str(race.index)
            + ";"
            + str(race.heat)
            + ";"
            + str(race.no_of_contestants)
            + ";"
            + str(race.rule)
        )
