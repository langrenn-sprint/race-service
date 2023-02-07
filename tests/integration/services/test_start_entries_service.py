"""Integration test cases for the start_entries service."""
from copy import deepcopy
from datetime import datetime
from typing import Any

import pytest
from pytest_mock import MockFixture

from race_service.adapters import StartEntryNotFoundException
from race_service.models import StartEntry
from race_service.services import (
    IllegalValueException,
    StartEntriesService,
)
from race_service.services.start_entries_service import (
    CouldNotCreateStartEntryException,
)


@pytest.fixture
async def new_start_entry() -> StartEntry:
    """Create a mock start_entry object."""
    return StartEntry(
        startlist_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        race_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=1,
        starting_position=1,
        scheduled_start_time=datetime.fromisoformat("2021-11-04T15:29:00"),
        name="First Contestant",
        club="Lyn Ski",
    )


@pytest.fixture
async def start_entry_mock() -> StartEntry:
    """Create a mock start_entry object."""
    return StartEntry(
        id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        startlist_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        race_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=1,
        starting_position=1,
        scheduled_start_time=datetime.fromisoformat("2021-11-04T15:29:00"),
        name="First Contestant",
        club="Lyn Ski",
        status=None,
        changelog=None,
    )


@pytest.mark.integration
async def test_create_start_entry(
    event_loop: Any,
    mocker: MockFixture,
    new_start_entry: StartEntry,
    start_entry_mock: StartEntry,
) -> None:
    """Should return Created, location header."""
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=start_entry_mock.id,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=start_entry_mock.id,
    )

    id = await StartEntriesService.create_start_entry(
        db=None, start_entry=new_start_entry
    )
    assert id == start_entry_mock.id


@pytest.mark.integration
async def test_update_start_entry(
    event_loop: Any,
    mocker: MockFixture,
    new_start_entry: StartEntry,
    start_entry_mock: StartEntry,
) -> None:
    """Should return a truthy result."""
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry_mock,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=True,
    )
    updated_start_entry = deepcopy(new_start_entry)
    updated_start_entry.id = start_entry_mock.id
    assert start_entry_mock.id
    result = await StartEntriesService.update_start_entry(
        db=None, id=start_entry_mock.id, start_entry=updated_start_entry
    )
    assert result


@pytest.mark.integration
async def test_delete_start_entry(
    event_loop: Any,
    mocker: MockFixture,
    start_entry_mock: StartEntry,
) -> None:
    """Should return a truthy result."""
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry_mock,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
    )
    assert start_entry_mock.id
    result = await StartEntriesService.delete_start_entry(
        db=None, id=start_entry_mock.id
    )
    assert result


# Bad cases


@pytest.mark.integration
async def test_create_start_entry_input_id(
    event_loop: Any,
    mocker: MockFixture,
    new_start_entry: StartEntry,
    start_entry_mock: StartEntry,
) -> None:
    """Should raise IllegalValueException."""
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=start_entry_mock.id,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=start_entry_mock.id,
    )
    start_entry_with_id = deepcopy(new_start_entry)
    start_entry_with_id.id = start_entry_mock.id

    with pytest.raises(IllegalValueException):
        await StartEntriesService.create_start_entry(
            db=None, start_entry=start_entry_with_id
        )


@pytest.mark.integration
async def test_create_start_entry_adapter_fails(
    event_loop: Any,
    mocker: MockFixture,
    new_start_entry: StartEntry,
    start_entry_mock: StartEntry,
) -> None:
    """Should raise IllegalValueException."""
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=start_entry_mock.id,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=None,
    )

    with pytest.raises(CouldNotCreateStartEntryException):
        await StartEntriesService.create_start_entry(
            db=None, start_entry=new_start_entry
        )


@pytest.mark.integration
async def test_update_start_entry_not_found(
    event_loop: Any,
    mocker: MockFixture,
    new_start_entry: StartEntry,
    start_entry_mock: StartEntry,
) -> None:
    """Should raise StartEntryNotFoundException."""
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=StartEntryNotFoundException(f"StartEntry with id {id} not found"),
    )
    updated_start_entry = deepcopy(new_start_entry)
    updated_start_entry.id = start_entry_mock.id

    assert start_entry_mock.id
    with pytest.raises(StartEntryNotFoundException):
        await StartEntriesService.update_start_entry(
            db=None, id=start_entry_mock.id, start_entry=updated_start_entry
        )


@pytest.mark.integration
async def test_update_start_entry_wrong_id(
    event_loop: Any,
    mocker: MockFixture,
    new_start_entry: StartEntry,
    start_entry_mock: StartEntry,
) -> None:
    """Should raise StartEntryNotFoundException."""
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry_mock,
    )
    updated_start_entry = deepcopy(new_start_entry)
    updated_start_entry.id = "wrong_id"

    assert start_entry_mock.id
    with pytest.raises(IllegalValueException):
        await StartEntriesService.update_start_entry(
            db=None, id=start_entry_mock.id, start_entry=updated_start_entry
        )


@pytest.mark.integration
async def test_delete_start_entry_not_found(
    event_loop: Any,
    mocker: MockFixture,
    start_entry_mock: StartEntry,
) -> None:
    """Should raise StartEntryNotFoundException."""
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=StartEntryNotFoundException(f"StartEntry with id {id} not found"),
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
    )

    assert start_entry_mock.id
    with pytest.raises(StartEntryNotFoundException):
        await StartEntriesService.delete_start_entry(db=None, id=start_entry_mock.id)
