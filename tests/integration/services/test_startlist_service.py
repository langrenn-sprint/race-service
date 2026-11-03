"""Integration test cases for the startlist service."""

from copy import deepcopy

import pytest
from pytest_mock import MockFixture

from app.models import Startlist
from app.services import (
    CouldNotCreateStartlistError,
    IllegalValueError,
    StartlistAllreadyExistError,
    StartlistsService,
)
from app.services.startlists_service import StartlistNotFoundError


@pytest.fixture
async def new_startlist() -> Startlist:
    """Create a startlist object."""
    return Startlist(
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        no_of_contestants=8,
        start_entries=[
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
    )


@pytest.fixture
async def startlist() -> Startlist:
    """Create a startlist object."""
    return Startlist(
        id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        no_of_contestants=8,
        start_entries=[
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
    )


@pytest.fixture
async def startlist_mock() -> Startlist:
    """Create a startlist object."""
    return Startlist(
        id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        no_of_contestants=8,
        start_entries=[
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_startlist_allready_exist(
    mocker: MockFixture,
    new_startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise IllegalValueError."""
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[startlist_mock],
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=True,
    )

    with pytest.raises(StartlistAllreadyExistError):
        await StartlistsService.create_startlist(startlist=new_startlist)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_startlist_adapter_fails(
    mocker: MockFixture,
    new_startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise IllegalValueError."""
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=None,
    )

    with pytest.raises(CouldNotCreateStartlistError):
        await StartlistsService.create_startlist(startlist=new_startlist)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_startlist_change_id(
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise IllegalValueError."""
    startlist_mock_with_other_id = deepcopy(startlist_mock)
    startlist_mock_with_other_id.id = "2b920f5c-eb82-5655-bd13-2001e5f0683e"
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist_mock_with_other_id,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    with pytest.raises(IllegalValueError):
        await StartlistsService.update_startlist(
            id_=startlist_mock_with_other_id.id, startlist=startlist
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_startlist_not_found(
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise StartlistNotFoundError."""
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    assert startlist_mock.id
    with pytest.raises(StartlistNotFoundError):
        await StartlistsService.update_startlist(
            id_=startlist_mock.id, startlist=startlist
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_startlist_not_found(
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Startlist,
) -> None:
    """Should raise StartlistNotFoundError."""
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=True,
    )

    assert startlist_mock.id
    with pytest.raises(StartlistNotFoundError):
        await StartlistsService.delete_startlist(
            id_=startlist_mock.id,
        )
