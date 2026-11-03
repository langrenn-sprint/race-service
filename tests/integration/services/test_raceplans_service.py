"""Integration test cases for the raceplan service."""

import pytest
from pytest_mock import MockFixture

from app.adapters import RaceplanNotFoundError
from app.models import Raceplan
from app.services import (
    RaceplanAllreadyExistError,
    RaceplansService,
)


@pytest.fixture
async def new_raceplan() -> Raceplan:
    """Create a race object."""
    return Raceplan(
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        races=[
            "f910dc1f-18da-50b1-948b-c847165a0556",
            "fa9e1174-f861-5300-a867-1cc364621b5c",
            "e222b1af-b820-5165-a2ad-ae76db9c9456",
            "551c94af-eb9d-58b5-99d6-02299bd6e363",
            "073337a5-72d4-54e1-b312-7e5af8dc24bd",
            "0e2c8c52-34cd-55da-afd2-0d780d814796",
            "ca321c9b-cfb6-5097-bff8-3f90748d1202",
            "4ca41147-c2ec-51cf-a250-eceff60a4942",
        ],
        no_of_contestants=8,
    )


@pytest.fixture
async def raceplan() -> Raceplan:
    """Create a race object."""
    return Raceplan(
        id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        races=[
            "f910dc1f-18da-50b1-948b-c847165a0556",
            "fa9e1174-f861-5300-a867-1cc364621b5c",
            "e222b1af-b820-5165-a2ad-ae76db9c9456",
            "551c94af-eb9d-58b5-99d6-02299bd6e363",
            "073337a5-72d4-54e1-b312-7e5af8dc24bd",
            "0e2c8c52-34cd-55da-afd2-0d780d814796",
            "ca321c9b-cfb6-5097-bff8-3f90748d1202",
            "4ca41147-c2ec-51cf-a250-eceff60a4942",
        ],
        no_of_contestants=8,
    )


@pytest.fixture
async def raceplan_mock() -> Raceplan:
    """Create a raceplan object."""
    return Raceplan(
        id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        no_of_contestants=8,
        races=[
            "f910dc1f-18da-50b1-948b-c847165a0556",
            "fa9e1174-f861-5300-a867-1cc364621b5c",
            "e222b1af-b820-5165-a2ad-ae76db9c9456",
            "551c94af-eb9d-58b5-99d6-02299bd6e363",
            "073337a5-72d4-54e1-b312-7e5af8dc24bd",
            "0e2c8c52-34cd-55da-afd2-0d780d814796",
            "ca321c9b-cfb6-5097-bff8-3f90748d1202",
            "4ca41147-c2ec-51cf-a250-eceff60a4942",
        ],
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_raceplan_allready_exist(
    mocker: MockFixture,
    new_raceplan: Raceplan,
    raceplan_mock: Raceplan,
) -> None:
    """Should raise IllegalValueError."""
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_mock],
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=True,
    )

    with pytest.raises(RaceplanAllreadyExistError):
        await RaceplansService.create_raceplan(raceplan=new_raceplan)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_raceplan_not_found(
    mocker: MockFixture,
    new_raceplan: Raceplan,
    raceplan_mock: Raceplan,
) -> None:
    """Should raise RaceplanNotFoundError."""
    raceplan_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        side_effect=RaceplanNotFoundError(f"Raceplan with id {raceplan_id} not found."),
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.delete_raceplan",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    with pytest.raises(RaceplanNotFoundError):
        await RaceplansService.delete_raceplan(id_=raceplan_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_race_adapter_fails(
    mocker: MockFixture,
    new_raceplan: Raceplan,
    raceplan_mock: dict,
) -> None:
    """Should return None."""
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=None,
    )

    result = await RaceplansService.create_raceplan(raceplan=new_raceplan)

    assert result is None
