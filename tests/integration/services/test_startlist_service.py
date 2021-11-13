"""Integration test cases for the startlist service."""
from copy import deepcopy
from typing import Any, Dict

import pytest
from pytest_mock import MockFixture

from race_service.models import Startlist
from race_service.services import (
    IllegalValueException,
    StartlistsService,
)
from race_service.services.startlists_service import StartlistNotFoundException


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
async def startlist_mock() -> Dict:
    """Create a startlist object."""
    return {
        "id": "startlist_1",
        "event_id": "event_1",
        "no_of_contestants": 8,
        "start_entries": ["11", "22", "33", "44", "55", "66", "77", "88"],
    }


@pytest.mark.integration
async def test_update_startlist_change_id(
    loop: Any,
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Dict,
) -> None:
    """Should raise IllegalValueException."""
    startlist_mock_with_other_id = deepcopy(startlist_mock)
    startlist_mock_with_other_id["id"] = "different_id"
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
            db=None, id=startlist_mock["id"], startlist=startlist
        )


@pytest.mark.integration
async def test_update_startlist_not_found(
    loop: Any,
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Dict,
) -> None:
    """Should raise StartlistNotFoundException."""
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    with pytest.raises(StartlistNotFoundException):
        await StartlistsService.update_startlist(
            db=None, id=startlist_mock["id"], startlist=startlist
        )


@pytest.mark.integration
async def test_delete_startlist_not_found(
    loop: Any,
    mocker: MockFixture,
    startlist: Startlist,
    startlist_mock: Dict,
) -> None:
    """Should raise StartlistNotFoundException."""
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=True,
    )

    with pytest.raises(StartlistNotFoundException):
        await StartlistsService.delete_startlist(
            db=None,
            id=startlist_mock["id"],
        )
