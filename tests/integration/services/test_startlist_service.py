"""Integration test cases for the startlist service."""
from copy import deepcopy

import pytest
from pytest_mock import MockFixture

from race_service.models import Startlist
from race_service.services import (
    CouldNotCreateStartlistException,
    IllegalValueException,
    StartlistAllreadyExistException,
    StartlistsService,
)
from race_service.services.startlists_service import StartlistNotFoundException


@pytest.fixture
async def new_startlist() -> Startlist:
    """Create a startlist object."""
    return Startlist(
        event_id="event_1",
        no_of_contestants=8,
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
    )


@pytest.fixture
async def startlist() -> Startlist:
    """Create a startlist object."""
    return Startlist(
        id="startlist_1",
        event_id="event_1",
        no_of_contestants=8,
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
    )


@pytest.fixture
async def startlist_mock() -> Startlist:
    """Create a startlist object."""
    return Startlist(
        id="startlist_1",
        event_id="event_1",
        no_of_contestants=8,
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_startlist_input_id(
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise IllegalValueException."""
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=True,
    )

    with pytest.raises(IllegalValueException):
        await StartlistsService.create_startlist(db=None, startlist=startlist)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_startlist_allready_exist(
    mocker: MockFixture,
    new_startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise IllegalValueException."""
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[startlist_mock],
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=True,
    )

    with pytest.raises(StartlistAllreadyExistException):
        await StartlistsService.create_startlist(db=None, startlist=new_startlist)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_startlist_adapter_fails(
    mocker: MockFixture,
    new_startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise IllegalValueException."""
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=None,
    )

    with pytest.raises(CouldNotCreateStartlistException):
        await StartlistsService.create_startlist(db=None, startlist=new_startlist)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_startlist_change_id(
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise IllegalValueException."""
    startlist_mock_with_other_id = deepcopy(startlist_mock)
    startlist_mock_with_other_id.id = "different_id"
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist_mock_with_other_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    with pytest.raises(IllegalValueException):
        await StartlistsService.update_startlist(
            db=None, id=startlist_mock_with_other_id.id, startlist=startlist
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_startlist_not_found(
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise StartlistNotFoundException."""
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundException(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    assert startlist_mock.id
    with pytest.raises(StartlistNotFoundException):
        await StartlistsService.update_startlist(
            db=None, id=startlist_mock.id, startlist=startlist
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_startlist_not_found(
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise StartlistNotFoundException."""
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundException(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=True,
    )

    assert startlist_mock.id
    with pytest.raises(StartlistNotFoundException):
        await StartlistsService.delete_startlist(
            db=None,
            id=startlist_mock.id,
        )
