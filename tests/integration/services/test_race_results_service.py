"""Integration test cases for the race_results service."""
from datetime import datetime

import pytest
from pytest_mock import MockFixture

from race_service.adapters import RaceResultNotFoundException
from race_service.models import IndividualSprintRace, RaceResult, StartEntry, TimeEvent
from race_service.services import (
    RaceResultsService,
    TimeEventDoesNotReferenceRaceException,
    TimeEventIsNotIdentifiableException,
)


@pytest.fixture
async def time_event() -> TimeEvent:
    """Create a time-event object."""
    return TimeEvent(
        id="time_event_1",
        bib=1,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        race_id="race_1",
        race="race_name",
        rank=1,
        next_race="semi_name1",
        next_race_id="semi_1",
        next_race_position=1,
        status="OK",
        changelog=[],
    )


@pytest.fixture
async def time_event_with_no_id() -> TimeEvent:
    """Create a time-event object."""
    return TimeEvent(
        bib=1,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        race_id="race_1",
        race="race_name",
        rank=1,
        next_race="semi_name1",
        next_race_id="semi_1",
        next_race_position=1,
        status="OK",
        changelog=[],
    )


@pytest.fixture
async def time_event_with_no_race_id() -> TimeEvent:
    """Create a time-event object."""
    return TimeEvent(
        id="time_event_1",
        bib=1,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        rank=1,
        next_race="semi_name1",
        next_race_id="semi_1",
        next_race_position=1,
        status="OK",
        changelog=[],
    )


@pytest.fixture
async def start_entry_mock() -> StartEntry:
    """Create a mock start_entry object."""
    return StartEntry(
        id="start_entry_1",
        race_id="race_1",
        startlist_id="startlist_1",
        bib=1,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        starting_position=1,
        status="",
        changelog=[],
    )


@pytest.fixture
async def race_mock() -> IndividualSprintRace:
    """Create a mock race object."""
    return IndividualSprintRace(
        id="race_1",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="raceplan_1",
        start_entries=["start_entry_1"],
        results={"Start": "race_result_1", "Finish": "race_result_2"},
        round="Q",
        index="",
        heat=1,
        rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
        datatype="individual_sprint",
    )


@pytest.fixture
async def race_mock_without_results() -> IndividualSprintRace:
    """Create a mock race object."""
    return IndividualSprintRace(
        id="race_1",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="raceplan_1",
        start_entries=["start_entry_1"],
        results={},
        round="Q",
        index="",
        heat=1,
        rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
        datatype="individual_sprint",
    )


@pytest.fixture
async def race_result_mock() -> RaceResult:
    """Create a mock race-result object."""
    return RaceResult(
        id="race_result_2",
        race_id="race_1",
        timing_point="Finish",
        no_of_contestants=2,
        ranking_sequence=["time_event_1", "time_event_2"],
        status=0,
    )


@pytest.fixture
async def race_result_empty_ranking_sequence_mock() -> RaceResult:
    """Create a mock race-result object."""
    return RaceResult(
        id="race_result_1",
        race_id="race_1",
        timing_point="Start",
        no_of_contestants=2,
        ranking_sequence=[],
        status=0,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_time_event_to_race_result(
    mocker: MockFixture,
    time_event: TimeEvent,
    race_mock: IndividualSprintRace,
    start_entry_mock: StartEntry,
    race_result_mock: RaceResult,
) -> None:
    """Should return Created, location header."""
    mocker.patch(
        "race_service.services.race_results_service.create_id",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_mock,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",  # noqa: B950
        return_value=[race_result_mock],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_mock.id,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_mock],
    )

    id = await RaceResultsService.add_time_event_to_race_result(
        db=None, time_event=time_event
    )
    assert id == race_result_mock.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_time_event_to_race_result_race_does_not_have_any_results(
    mocker: MockFixture,
    time_event: TimeEvent,
    race_mock_without_results: IndividualSprintRace,
    start_entry_mock: StartEntry,
    race_result_mock: RaceResult,
) -> None:
    """Should return Created, location header."""
    mocker.patch(
        "race_service.services.race_results_service.create_id",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_mock_without_results,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",  # noqa: B950
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_mock_without_results.id,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_mock],
    )

    id = await RaceResultsService.add_time_event_to_race_result(
        db=None, time_event=time_event
    )
    assert id == race_result_mock.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_time_event_to_race_result_no_ranking_sequence(
    mocker: MockFixture,
    time_event: TimeEvent,
    start_entry_mock: StartEntry,
    race_mock: IndividualSprintRace,
    race_result_empty_ranking_sequence_mock: RaceResult,
) -> None:
    """Should return an id."""
    mocker.patch(
        "race_service.services.race_results_service.create_id",
        return_value=race_result_empty_ranking_sequence_mock.id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_empty_ranking_sequence_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_mock,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",  # noqa: B950
        return_value=[race_result_empty_ranking_sequence_mock],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_empty_ranking_sequence_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_mock.id,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_mock],
    )

    id = await RaceResultsService.add_time_event_to_race_result(
        db=None, time_event=time_event
    )
    assert id == race_result_empty_ranking_sequence_mock.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_time_event_to_race_result_no_id(
    mocker: MockFixture,
    time_event_with_no_id: TimeEvent,
    race_mock: IndividualSprintRace,
    race_result_mock: RaceResult,
) -> None:
    """Should raise TimeEventIsNotIdentifiableException."""
    mocker.patch(
        "race_service.services.race_results_service.create_id",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_mock,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",  # noqa: B950
        return_value=[race_result_mock],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_mock.id,
    )

    with pytest.raises(TimeEventIsNotIdentifiableException):
        await RaceResultsService.add_time_event_to_race_result(
            db=None, time_event=time_event_with_no_id
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_time_event_to_race_race_does_not_exist(
    mocker: MockFixture,
    time_event_with_no_race_id: TimeEvent,
    race_mock: IndividualSprintRace,
    race_result_mock: RaceResult,
) -> None:
    """Should raise TimeEventDoesNotReferenceRaceException."""
    mocker.patch(
        "race_service.services.race_results_service.create_id",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_mock,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",  # noqa: B950
        return_value=[race_result_mock],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_mock.id,
    )

    with pytest.raises(TimeEventDoesNotReferenceRaceException):
        await RaceResultsService.add_time_event_to_race_result(
            db=None, time_event=time_event_with_no_race_id
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result_race_result_not_found(
    mocker: MockFixture,
    race_mock: IndividualSprintRace,
    race_result_mock: RaceResult,
) -> None:
    """Should raise RaceResultNotFoundException."""
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundException(f"RaceResult with id {id} not found"),
    )

    with pytest.raises(RaceResultNotFoundException):
        await RaceResultsService.delete_race_result(db=None, id=race_result_mock.id)
