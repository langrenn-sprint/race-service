"""Integration test cases for the race service."""

from datetime import datetime

import pytest
from pytest_mock import MockFixture

from app.models import Race
from app.services import (
    RacesService,
)


@pytest.fixture
async def new_race() -> Race:
    """Create a race object."""
    return Race(
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-11-17T20:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
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
        results={},
    )


@pytest.fixture
async def race() -> Race:
    """Create a race object."""
    return Race(
        id="f910dc1f-18da-50b1-948b-c847165a0556",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-11-17T20:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
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
        results={},
    )


@pytest.fixture
async def race_mock() -> dict:
    """Create a race object."""
    return {
        "id": "f910dc1f-18da-50b1-948b-c847165a0556",
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 8,
        "max_no_of_contestants": 10,
        "event_id": "e726010d-728b-5516-a930-dd8e9b210255",
        "raceplan_id": "b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
        "start_entries": [
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
        "results": {"Finish": "50b75bea-866a-50fc-bde0-78cc68b04fec"},
        "round": "Q",
        "index": "",
        "heat": 1,
        "rule": {"A": {"S": {"A": 10, "C": 0}}},
        "datatype": "individual_sprint",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_race_adapter_fails(
    mocker: MockFixture,
    new_race: Race,
    race_mock: dict,
) -> None:
    """Should raise IllegalValueError."""
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.create_race",
        return_value=None,
    )

    result = await RacesService.create_race(race=new_race)

    assert result is None
