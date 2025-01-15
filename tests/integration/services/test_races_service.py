"""Integration test cases for the race service."""

from datetime import datetime

import pytest
from pytest_mock import MockFixture

from race_service.models import Race
from race_service.services import (
    IllegalValueError,
    RacesService,
)


@pytest.fixture
async def new_race() -> Race:
    """Create a race object."""
    return Race(
        id="",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-11-17T20:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="raceplan_1",
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
        results={},
    )


@pytest.fixture
async def race() -> Race:
    """Create a race object."""
    return Race(
        id="race_1",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-11-17T20:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="raceplan_1",
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
        results={},
    )


@pytest.fixture
async def race_mock() -> dict:
    """Create a race object."""
    return {
        "id": "race_1",
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 8,
        "max_no_of_contestants": 10,
        "event_id": "event_1",
        "raceplan_id": "raceplan_1",
        "start_entries": ["11", "22", "33", "44", "55", "66", "77", "88"],
        "results": {"Finish": "race_result_1"},
        "round": "Q",
        "index": "",
        "heat": 1,
        "rule": {"A": {"S": {"A": 10, "C": 0}}},
        "datatype": "individual_sprint",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_race_input_id(
    mocker: MockFixture,
    race: Race,
    race_mock: dict,
) -> None:
    """Should raise IllegalValueError."""
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=True,
    )

    with pytest.raises(IllegalValueError):
        await RacesService.create_race(db=None, race=race)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_race_adapter_fails(
    mocker: MockFixture,
    new_race: Race,
    race_mock: dict,
) -> None:
    """Should raise IllegalValueError."""
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=None,
    )

    result = await RacesService.create_race(db=None, race=new_race)

    assert result is None
