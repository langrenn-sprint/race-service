"""Integration test cases for the raceplans route."""
import os
from typing import Any, Dict, List
import uuid

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
import jwt
import pytest
from pytest_mock import MockFixture


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.fixture
async def request_body() -> dict:
    """Create a mock request_body object."""
    return {"event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95"}


@pytest.fixture
async def event() -> Dict[str, Any]:
    """An event object for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint",
        "competition_format": "Individual Sprint",
        "date_of_event": "2021-08-31",
        "time_of_event": "09:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def format_configuration() -> Dict[str, Any]:
    """A format configuration for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_groups": "00:15:00",
        "time_between_rounds": "00:10:00",
        "time_between_heats": "00:02:30",
        "max_no_of_contestants_in_raceclass": 80,
        "max_no_of_contestants_in_race": 10,
        "datatype": "individual_sprint",
    }


@pytest.fixture
async def raceclasses() -> List[Dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G13",
            "ageclass_name": "G 13 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 7,
            "group": 1,
            "order": 1,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G14",
            "ageclass_name": "G 14 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 8,
            "group": 1,
            "order": 2,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J13",
            "ageclass_name": "J 13 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 17,
            "group": 1,
            "order": 3,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J14",
            "ageclass_name": "J 14 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 25,
            "group": 1,
            "order": 4,
        },
        {
            "id": "590e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclass_name": "G 15 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 33,
            "group": 2,
            "order": 1,
        },
        {
            "id": "690e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclass_name": "G 16 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 41,
            "group": 2,
            "order": 2,
        },
        {
            "id": "790e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclass_name": "J 15 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 49,
            "group": 2,
            "order": 3,
        },
        {
            "id": "890e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclass_name": "J 16 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 57,
            "group": 2,
            "order": 4,
        },
    ]


@pytest.mark.integration
async def test_generate_raceplan_for_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    format_configuration: dict,
    raceclasses: List[dict],
    request_body: dict,
) -> None:
    """Should return 201 Created, location header."""
    RACEPLAN_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value={"id": RACEPLAN_ID},
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=str(uuid.uuid4()),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_format_configuration",
        return_value=format_configuration,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.post(
            "/raceplans/generate-raceplan-for-event", headers=headers, json=request_body
        )
        assert resp.status == 201
        assert f"/raceplans/{RACEPLAN_ID}" in resp.headers[hdrs.LOCATION]


@pytest.fixture
async def raceclass_with_more_than_max_contestants() -> List[Dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G13",
            "ageclass_name": "G 13 år",
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 81,
            "group": 1,
            "order": 1,
        },
    ]


@pytest.mark.integration
async def test_generate_raceplan_for_event_exceeds_max_no_of_contestants_in_raceclass(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    format_configuration: dict,
    raceclass_with_more_than_max_contestants: List[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    RACEPLAN_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value={"id": RACEPLAN_ID},
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=str(uuid.uuid4()),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_format_configuration",
        return_value=format_configuration,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclass_with_more_than_max_contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.post(
            "/raceplans/generate-raceplan-for-event", headers=headers, json=request_body
        )
        assert resp.status == 400
        body = await resp.json()
        assert "Unsupported value for no of contestants" in body["detail"]
