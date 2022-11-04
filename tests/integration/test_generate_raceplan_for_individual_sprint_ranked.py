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
async def race_config() -> List[Dict[str, Any]]:
    """A race_config used in format_configuration."""
    return [
        {
            "max_no_of_contestants": 7,
            "rounds": ["Q", "F"],
            "no_of_heats": {
                "Q": {"A": 1},
                "F": {"A": 1, "B": 0, "C": 0},
            },
            "from_to": {
                "Q": {"A": {"F": {"A": "ALL", "B": 0}}, "C": {"F": {"C": 0}}},
            },
        },
        {
            "max_no_of_contestants": 16,
            "rounds": ["Q", "F"],
            "no_of_heats": {
                "Q": {"A": 2},
                "F": {"A": 1, "B": 1, "C": 0},
            },
            "from_to": {
                "Q": {"A": {"F": {"A": 4, "B": "REST"}}, "C": {"F": {"C": 0}}},
            },
        },
        {
            "max_no_of_contestants": 24,
            "rounds": ["Q", "S", "F"],
            "no_of_heats": {
                "Q": {"A": 3},
                "S": {"A": 2, "C": 0},
                "F": {"A": 1, "B": 1, "C": 1},
            },
            "from_to": {
                "Q": {"A": {"S": {"A": 5, "C": 0}, "F": {"C": "REST"}}},
                "S": {"A": {"F": {"A": 4, "B": "REST"}}, "C": {"F": {"C": 0}}},
            },
        },
        {
            "max_no_of_contestants": 32,
            "rounds": ["Q", "S", "F"],
            "no_of_heats": {
                "Q": {"A": 4},
                "S": {"A": 2, "C": 2},
                "F": {"A": 1, "B": 1, "C": 1},
            },
            "from_to": {
                "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                "S": {"A": {"F": {"A": 4, "B": "REST"}}, "C": {"F": {"C": 4}}},
            },
        },
        {
            "max_no_of_contestants": 40,
            "rounds": ["Q", "S", "F"],
            "no_of_heats": {
                "Q": {"A": 6},
                "S": {"A": 4, "C": 2},
                "F": {"A": 1, "B": 1, "C": 1},
            },
            "from_to": {
                "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 4}}},
            },
        },
        {
            "max_no_of_contestants": 48,
            "rounds": ["Q", "S", "F"],
            "no_of_heats": {
                "Q": {"A": 6},
                "S": {"A": 4, "C": 4},
                "F": {"A": 1, "B": 1, "C": 1},
            },
            "from_to": {
                "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 2}}},
            },
        },
        {
            "max_no_of_contestants": 56,
            "rounds": ["Q", "S", "F"],
            "no_of_heats": {
                "Q": {"A": 7},
                "S": {"A": 4, "C": 4},
                "F": {"A": 1, "B": 1, "C": 1},
            },
            "from_to": {
                "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 2}}},
            },
        },
        {
            "max_no_of_contestants": 80,
            "rounds": ["Q", "S", "F"],
            "no_of_heats": {
                "Q": {"A": 8},
                "S": {"A": 4, "C": 4},
                "F": {"A": 1, "B": 1, "C": 1},
            },
            "from_to": {
                "Q": {"A": {"S": {"A": 4, "C": "REST"}}},
                "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 2}}},
            },
        },
    ]


@pytest.fixture
async def format_configuration(race_config: Dict) -> Dict[str, Any]:
    """A format configuration for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_groups": "00:15:00",
        "time_between_rounds": "00:10:00",
        "time_between_heats": "00:02:30",
        "rounds_ranked_classes": ["Q", "S", "F"],
        "rounds_non_ranked_classes": ["R1", "R2"],
        "max_no_of_contestants_in_raceclass": 80,
        "max_no_of_contestants_in_race": 10,
        "datatype": "individual_sprint",
        "race_config_non_ranked": None,
        "race_config_ranked": race_config,
    }


@pytest.fixture
async def raceclasses() -> List[Dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G13",
            "ageclasses": ["G 13 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 7,
            "ranking": True,
            "group": 1,
            "order": 1,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G14",
            "ageclasses": ["G 14 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 8,
            "ranking": True,
            "group": 1,
            "order": 2,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J13",
            "ageclasses": ["J 13 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 17,
            "ranking": True,
            "group": 1,
            "order": 3,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J14",
            "ageclasses": ["J 14 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 25,
            "ranking": True,
            "group": 1,
            "order": 4,
        },
        {
            "id": "590e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclasses": ["G 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 33,
            "ranking": True,
            "group": 2,
            "order": 1,
        },
        {
            "id": "690e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 41,
            "ranking": True,
            "group": 2,
            "order": 2,
        },
        {
            "id": "790e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclasses": ["J 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 49,
            "ranking": True,
            "group": 2,
            "order": 3,
        },
        {
            "id": "890e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclasses": ["J 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 57,
            "ranking": True,
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
        m.post("http://users.example.com:8080/authorize", status=204)

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
            "ageclasses": ["G 13 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 81,
            "ranking": True,
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
        m.post("http://users.example.com:8080/authorize", status=204)

        resp = await client.post(
            "/raceplans/generate-raceplan-for-event", headers=headers, json=request_body
        )
        assert resp.status == 400
        body = await resp.json()
        assert "Unsupported value for no of contestants" in body["detail"]
