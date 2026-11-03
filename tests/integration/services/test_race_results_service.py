"""Integration test cases for the race_results service."""

from datetime import datetime

import pytest
from pytest_mock import MockFixture

from app.adapters import RaceResultNotFoundError
from app.models import IndividualSprintRace, RaceResult, StartEntry, TimeEvent
from app.services import (
    RaceResultsService,
    TimeEventDoesNotReferenceRaceError,
)


@pytest.fixture
async def time_event() -> TimeEvent:
    """Create a time-event object."""
    return TimeEvent(
        id="1ba641c0-ed88-5934-9b13-667d34430228",
        bib=1,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        race="race_name",
        rank=1,
        next_race="semi_name1",
        next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
        next_race_position=1,
        status="OK",
        changelog=[],
    )


@pytest.fixture
async def time_event_with_no_id() -> TimeEvent:
    """Create a time-event object."""
    return TimeEvent(
        bib=1,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        race="race_name",
        rank=1,
        next_race="semi_name1",
        next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
        next_race_position=1,
        status="OK",
        changelog=[],
    )


@pytest.fixture
async def time_event_with_no_race_id() -> TimeEvent:
    """Create a time-event object."""
    return TimeEvent(
        id="1ba641c0-ed88-5934-9b13-667d34430228",
        bib=1,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        name="Petter Propell",
        club="Barnehagen",
        timing_point="Finish",
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        rank=1,
        next_race="semi_name1",
        next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
        next_race_position=1,
        status="OK",
        changelog=[],
    )


@pytest.fixture
async def start_entry_mock() -> StartEntry:
    """Create a mock start_entry object."""
    return StartEntry(
        id="621461f5-91a2-5f82-99f9-ea72c3278b07",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
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
        id="f910dc1f-18da-50b1-948b-c847165a0556",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
        start_entries=["621461f5-91a2-5f82-99f9-ea72c3278b07"],
        results={
            "Start": "50b75bea-866a-50fc-bde0-78cc68b04fec",
            "Finish": "0f20fbb6-aebe-5b26-a568-bb5e2873b838",
        },
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
        id="f910dc1f-18da-50b1-948b-c847165a0556",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
        start_entries=["621461f5-91a2-5f82-99f9-ea72c3278b07"],
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
        id="0f20fbb6-aebe-5b26-a568-bb5e2873b838",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        timing_point="Finish",
        no_of_contestants=2,
        ranking_sequence=[
            "1ba641c0-ed88-5934-9b13-667d34430228",
            "5c369f7a-1967-5a65-91da-2f6f99e3e86d",
        ],
        status=0,
    )


@pytest.fixture
async def race_result_empty_ranking_sequence_mock() -> RaceResult:
    """Create a mock race-result object."""
    return RaceResult(
        id="50b75bea-866a-50fc-bde0-78cc68b04fec",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
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
        "app.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_mock,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result_mock],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_mock.id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_mock],
    )

    _id = await RaceResultsService.add_time_event_to_race_result(time_event=time_event)
    assert _id == race_result_mock.id


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
    create_race_result = mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_mock_without_results,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_mock_without_results.id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_mock],
    )

    _id = await RaceResultsService.add_time_event_to_race_result(time_event=time_event)
    # A new race-result is created, with a generated id:
    assert _id == create_race_result.call_args.args[0].id


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
        "app.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_empty_ranking_sequence_mock.id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_mock,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result_empty_ranking_sequence_mock],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_empty_ranking_sequence_mock.id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_mock.id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_mock],
    )

    _id = await RaceResultsService.add_time_event_to_race_result(time_event=time_event)
    assert _id == race_result_empty_ranking_sequence_mock.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_time_event_to_race_race_does_not_exist(
    mocker: MockFixture,
    time_event_with_no_race_id: TimeEvent,
    race_mock: IndividualSprintRace,
    race_result_mock: RaceResult,
) -> None:
    """Should raise TimeEventDoesNotReferenceRaceError."""
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_mock,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result_mock],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_mock.id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=race_mock.id,
    )

    with pytest.raises(TimeEventDoesNotReferenceRaceError):
        await RaceResultsService.add_time_event_to_race_result(
            time_event=time_event_with_no_race_id
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result_race_result_not_found(
    mocker: MockFixture,
    race_mock: IndividualSprintRace,
    race_result_mock: RaceResult,
) -> None:
    """Should raise RaceResultNotFoundError."""
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundError(
            f"RaceResult with id {race_result_mock.id} not found"
        ),
    )

    with pytest.raises(RaceResultNotFoundError):
        await RaceResultsService.delete_race_result(id_=race_result_mock.id)
