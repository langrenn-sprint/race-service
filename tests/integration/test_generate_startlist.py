"""Integration test cases for the startlists route."""

import os
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from typing import Any

import jwt
import pytest
from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
from pytest_mock import MockFixture

from race_service.adapters import (
    CompetitionFormatNotFoundError,
    ContestantsNotFoundError,
    EventNotFoundError,
    RaceclassesNotFoundError,
)
from race_service.models import IntervalStartRace, Raceplan

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
async def request_body() -> dict:
    """Create a mock request_body object."""
    return {"event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95"}


@pytest.fixture
async def event() -> dict[str, Any]:
    """An event object for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint",
        "competition_format": "Interval Start",
        "date_of_event": "2021-08-31",
        "time_of_event": "09:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def event_not_supported_competition_format() -> dict[str, Any]:
    """An event object for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint",
        "competition_format": "Not supported competition-format",
        "date_of_event": "2021-08-31",
        "time_of_event": "09:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def event_has_no_competition_format() -> dict[str, Any]:
    """An event object for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint",
        "date_of_event": "2021-08-31",
        "time_of_event": "09:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def competition_format() -> dict[str, Any]:
    """An competition-format for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Interval Start",
        "start_procedure": "Interval Start",
        "intervals": "00:00:30",
        "max_no_of_contestants_in_raceclass": 10000,
        "max_no_of_contestants_in_race": 10000,
    }


@pytest.fixture
async def raceclasses() -> list[dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclasses": ["G 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 1,
            "order": 2,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 1,
            "order": 4,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclasses": ["J 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 1,
            "order": 1,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclasses": ["J 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 2,
            "group": 1,
            "order": 3,
        },
    ]


@pytest.fixture
async def races(event: dict, competition_format: dict) -> list[IntervalStartRace]:
    """A list of races for testing."""
    return [
        IntervalStartRace(
            id="1",
            raceclass="J15",
            order=1,
            start_time=datetime.fromisoformat("2021-08-31 09:00:00"),
            no_of_contestants=2,
            max_no_of_contestants=competition_format["max_no_of_contestants_in_race"],
            event_id=event["id"],
            raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
            start_entries=[],
            results={},
            datatype="interval_start",
        ),
        IntervalStartRace(
            id="2",
            raceclass="G15",
            order=2,
            start_time=datetime.fromisoformat("2021-08-31 09:01:00"),
            no_of_contestants=2,
            max_no_of_contestants=competition_format["max_no_of_contestants_in_race"],
            event_id=event["id"],
            raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
            start_entries=[],
            results={},
            datatype="interval_start",
        ),
        IntervalStartRace(
            id="3",
            raceclass="J16",
            order=3,
            start_time=datetime.fromisoformat("2021-08-31 09:02:00"),
            no_of_contestants=2,
            max_no_of_contestants=competition_format["max_no_of_contestants_in_race"],
            event_id=event["id"],
            raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
            start_entries=[],
            results={},
            datatype="interval_start",
        ),
        IntervalStartRace(
            id="4",
            raceclass="G16",
            order=4,
            start_time=datetime.fromisoformat("2021-08-31 09:03:00"),
            no_of_contestants=2,
            max_no_of_contestants=competition_format["max_no_of_contestants_in_race"],
            event_id=event["id"],
            raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
            start_entries=[],
            results={},
            datatype="interval_start",
        ),
    ]


@pytest.fixture
async def raceplan_interval_start(
    event: dict, races: list[IntervalStartRace]
) -> Raceplan:
    """Create a mock raceplan object."""
    return Raceplan(
        event_id=event["id"],
        id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        no_of_contestants=8,
        races=[race.id for race in races],
    )


@pytest.fixture
async def contestants(event: dict, raceplan_interval_start: Raceplan) -> list[dict]:
    """Create a mock contestant list object."""
    return [
        {
            "bib": 1,
            "first_name": "Cont E.",
            "last_name": "Stant",
            "birth_date": "1970-01-01",
            "gender": "K",
            "ageclass": "J 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event["id"],
        },
        {
            "bib": 2,
            "first_name": "Conte E.",
            "last_name": "Stante",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "J 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event["id"],
        },
        {
            "bib": 3,
            "first_name": "Conta E.",
            "last_name": "Stanta",
            "birth_date": "1970-01-01",
            "gender": "K",
            "ageclass": "G 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event["id"],
        },
        {
            "bib": 4,
            "first_name": "Conti E.",
            "last_name": "Stanti",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "G 15 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event["id"],
        },
        {
            "bib": 5,
            "first_name": "AContA E.",
            "last_name": "AStanta",
            "birth_date": "1970-01-01",
            "gender": "K",
            "ageclass": "J 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event["id"],
        },
        {
            "bib": 6,
            "first_name": "AConte E.",
            "last_name": "AStante",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "J 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event["id"],
        },
        {
            "bib": 7,
            "first_name": "Contas E.",
            "last_name": "Stantas",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "G 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event["id"],
        },
        {
            "bib": 8,
            "first_name": "Contus E.",
            "last_name": "Stantus",
            "birth_date": "1970-01-01",
            "gender": "M",
            "ageclass": "G 16 år",
            "region": "Oslo Skikrets",
            "club": "Lyn Ski",
            "team": "Team Kollen",
            "email": "post@example.com",
            "event_id": event["id"],
        },
    ]


# bad cases
@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_request_body(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event", headers=headers
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_races_in_plan(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_contestants_bib_not_int(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    contestants_bib_not_int = deepcopy(contestants)
    contestants_bib_not_int[0]["bib"] = "1"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants_bib_not_int,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_contestants_bib_not_unique(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    contestants_bib_not_unique = deepcopy(contestants)
    contestants_bib_not_unique[1]["bib"] = 1
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants_bib_not_unique,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_contestants(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_contestants_error(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        side_effect=ContestantsNotFoundError("Contestants not found for event."),
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_raceplan(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST
        body = await resp.json()
        assert "No raceplan for event" in body["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_raceclasses_error(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        side_effect=RaceclassesNotFoundError("No raceclasses for event."),
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST
        body = await resp.json()
        assert "No raceclasses for event" in body["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_duplicate_raceplans(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 201 Created, location header."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start, raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST
        body = await resp.json()
        assert "Multiple raceplans for event " in body["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_contestants_differ_from_raceclasses(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceclasses_with_wrong_no_of_contestants = deepcopy(raceclasses)
    raceclasses_with_wrong_no_of_contestants[0]["no_of_contestants"] = 100000
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses_with_wrong_no_of_contestants,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST
        body = await resp.json()
        assert (
            "len(contestants) does not match number of contestants in raceclasses"
            in body["detail"]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_contestants_differ_from_raceplan(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_with_wrong_no_of_contestants = deepcopy(raceplan_interval_start)
    raceplan_with_wrong_no_of_contestants.no_of_contestants = 100000
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_with_wrong_no_of_contestants],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST
        body = await resp.json()
        assert (
            "len(contestants) does not match number of contestants in raceplan"
            in body["detail"]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_contestants_differ_from_races(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_races_with_wrong_no_of_contestants = deepcopy(raceplan_interval_start)
    races = deepcopy(races)
    race_with_wrong_number_of_contestants = races[-1]
    race_with_wrong_number_of_contestants.no_of_contestants = 100000
    raceplan_races_with_wrong_no_of_contestants.races[-1] = (
        race_with_wrong_number_of_contestants.id
    )
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_races_with_wrong_no_of_contestants],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST
        body = await resp.json()
        assert (
            "len(contestants) does not match sum of contestants in races"
            in body["detail"]
        )


# Not authenticated
@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_unauthorized(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 401 Unauthorized."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.UNAUTHORIZED


# Not found cases:
@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_already_has_startlist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[{"id": "blabladibla"}],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


# Not found cases:
@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_event_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 404 Not found."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        side_effect=EventNotFoundError("Event {event_id} not found."),
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_competition_format_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Not found."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        side_effect=CompetitionFormatNotFoundError("Competition format not found."),
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_raceclasses(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 404 Not found."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_no_competition_format(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_has_no_competition_format: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_has_no_competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_missing_intervals(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad Request."""
    competition_format_missing_intervals = deepcopy(competition_format)
    competition_format_missing_intervals.pop("intervals", None)
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format_missing_intervals,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_time_missing(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad request."""
    event_missing_time = deepcopy(event)
    event_missing_time.pop("time_of_event", None)
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_missing_time,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_date_missing(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad Request."""
    event_missing_date = deepcopy(event)
    event_missing_date.pop("date_of_event", None)
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_missing_date,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_invalid_date(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad Request."""
    event_invalid_date = deepcopy(event)
    event_invalid_date["date_of_event"] = "2021-13-32"
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_invalid_date,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_invalid_time(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad Request."""
    event_invalid_time = deepcopy(event)
    event_invalid_time["time_of_event"] = "15:67:99"
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_invalid_time,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST


# Not supported errors:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_startlist_for_event_competition_format_not_supported(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event_not_supported_competition_format: dict,
    competition_format: dict,
    raceclasses: list[dict],
    raceplan_interval_start: Raceplan,
    races: list[IntervalStartRace],
    contestants: list[dict],
    request_body: dict,
) -> None:
    """Should return 400 Bad Request."""
    raceplan_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event_not_supported_competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_raceplan_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_contestants",
        return_value=contestants,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(
            "/startlists/generate-startlist-for-event",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.BAD_REQUEST
