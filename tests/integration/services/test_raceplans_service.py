"""Integration test cases for the raceplan service."""
from typing import Any, Dict

import pytest
from pytest_mock import MockFixture

from race_service.adapters import RaceplanNotFoundException
from race_service.models import Raceplan
from race_service.services import (
    IllegalValueException,
    RaceplanAllreadyExistException,
    RaceplansService,
)


@pytest.fixture
async def new_raceplan() -> Raceplan:
    """Create a race object."""
    return Raceplan(
        event_id="event_1",
        races=[
            "race_1",
            "race_2",
            "race_3",
            "race_4",
            "race_5",
            "race_6",
            "race_7",
            "race_8",
        ],
        no_of_contestants=8,
    )


@pytest.fixture
async def raceplan() -> Raceplan:
    """Create a race object."""
    return Raceplan(
        id="raceplan_1",
        event_id="event_1",
        races=[
            "race_1",
            "race_2",
            "race_3",
            "race_4",
            "race_5",
            "race_6",
            "race_7",
            "race_8",
        ],
        no_of_contestants=8,
    )


@pytest.fixture
async def raceplan_mock() -> Raceplan:
    """Create a raceplan object."""
    return Raceplan(
        id="raceplan_1",
        event_id="event_1",
        no_of_contestants=8,
        races=[
            "race_1",
            "race_2",
            "race_3",
            "race_4",
            "race_5",
            "race_6",
            "race_7",
            "race_8",
        ],
    )


@pytest.mark.integration
async def test_create_race_input_id(
    event_loop: Any,
    mocker: MockFixture,
    raceplan: Raceplan,
    raceplan_mock: Dict,
) -> None:
    """Should raise IllegalValueException."""
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=True,
    )

    with pytest.raises(IllegalValueException):
        await RaceplansService.create_raceplan(db=None, raceplan=raceplan)


@pytest.mark.integration
async def test_create_raceplan_allready_exist(
    event_loop: Any,
    mocker: MockFixture,
    new_raceplan: Raceplan,
    raceplan_mock: Raceplan,
) -> None:
    """Should raise IllegalValueException."""
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_mock],
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=True,
    )

    with pytest.raises(RaceplanAllreadyExistException):
        await RaceplansService.create_raceplan(db=None, raceplan=new_raceplan)


@pytest.mark.integration
async def test_delete_raceplan_not_found(
    event_loop: Any,
    mocker: MockFixture,
    new_raceplan: Raceplan,
    raceplan_mock: Raceplan,
) -> None:
    """Should raise RaceplanNotFoundException."""
    RACEPLAN_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        side_effect=RaceplanNotFoundException(
            f"Raceplan with id {RACEPLAN_ID} not found."
        ),
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.delete_raceplan",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    with pytest.raises(RaceplanNotFoundException):
        await RaceplansService.delete_raceplan(db=None, id=RACEPLAN_ID)


@pytest.mark.integration
async def test_create_race_adapter_fails(
    event_loop: Any,
    mocker: MockFixture,
    new_raceplan: Raceplan,
    raceplan_mock: Dict,
) -> None:
    """Should return None."""
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=None,
    )

    result = await RaceplansService.create_raceplan(db=None, raceplan=new_raceplan)

    assert result is None
