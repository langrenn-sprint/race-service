"""Integration test cases for the time_events route."""

import os
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from json import dumps
from typing import Any

import jwt
import pytest
from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
from pytest_mock import MockFixture

from race_service.adapters import RaceNotFoundError, TimeEventNotFoundError
from race_service.models import (
    Changelog,
    IndividualSprintRace,
    RaceResult,
    StartEntry,
    TimeEvent,
)

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
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "user", "roles": ["user"]}
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
async def event() -> dict[str, Any]:
    """An event object for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint",
        "competition_format": "Interval Start",
        "date_of_event": "2021-08-31",
        "time_of_event": "09:00:00",
        "timezone": "Europe/Oslo",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def start_entry() -> StartEntry:
    """Create a mock start_entry object."""
    return StartEntry(
        id="start_entry_1",
        race_id="race_1",
        startlist_id="startlist_1",
        bib=1,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        starting_position=1,
        status="",
        changelog=[],
    )


@pytest.fixture
async def race() -> IndividualSprintRace:
    """Create a mock race object."""
    return IndividualSprintRace(
        id="race_1",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=0,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=["start_entry_1"],
        results={},
        round="Q",
        index="",
        heat=1,
        rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
        datatype="individual_sprint",
    )


@pytest.fixture
async def race_result() -> RaceResult:
    """Create a race_result object."""
    return RaceResult(
        id="race_result_1",
        race_id="race_1",
        timing_point="Finish",
        no_of_contestants=0,
        ranking_sequence=["290e70d5-0933-4af0-bb53-1d705ba7eb95"],
        status=0,
    )


@pytest.fixture
async def new_time_event() -> TimeEvent:
    """Create a time_event object."""
    return TimeEvent(
        bib=1,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="race_1",
        timing_point="Finish",
        rank=0,
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        next_race="semi_name1",
        next_race_id="semi_1",
        next_race_position=1,
        status="OK",
        changelog=[],
    )


@pytest.fixture
async def time_event() -> TimeEvent:
    """Create a mock time_event object."""
    return TimeEvent(
        id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        bib=1,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="race_1",
        timing_point="Finish",
        rank=0,
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        next_race="semi_name1",
        next_race_id="semi_1",
        next_race_position=1,
        status="OK",
        changelog=[
            Changelog(
                timestamp=datetime.fromisoformat("2021-11-08T22:06:30"),
                user_id="test",
                comment="hello",
            )
        ],
    )


@pytest.fixture
async def time_events() -> list[TimeEvent]:
    """Create a mock time_event object."""
    return [
        TimeEvent(
            id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
            bib=1,
            event_id="event_1",
            name="Petter Propell",
            club="Barnehagen",
            race="race_name",
            race_id="race_1",
            timing_point="Finish",
            rank=0,
            registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
            next_race="semi_name1",
            next_race_id="semi_1",
            next_race_position=1,
            status="OK",
            changelog=[
                Changelog(
                    timestamp=datetime.fromisoformat("2021-11-08T22:06:30"),
                    user_id="test",
                    comment="hello",
                )
            ],
        )
    ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    start_entry: StartEntry,
    race: dict,
    race_result: RaceResult,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 200 OK, and a body containing the new time-event."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
    )

    request_body = dumps(
        new_time_event.to_dict(), indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.OK

        body = await resp.json()
        assert body["status"] == "OK"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_race_result_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    start_entry: StartEntry,
    race: dict,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 200 OK, and a body containing the new time-event."""
    time_event_id = time_event.id
    race_result_id = "new_race_result"
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_id,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
    )

    request_body = dumps(
        new_time_event.to_dict(), indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.OK

        body = await resp.json()
        assert body["status"] == "OK"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_contestant_not_in_race(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    start_entry: StartEntry,
    race: dict,
    race_result: RaceResult,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 200 OK, and a body containing the new time-event."""
    time_event_id = time_event.id
    start_entry_wrong_bib = deepcopy(start_entry)
    start_entry_wrong_bib.bib = 1000

    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_wrong_bib],
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    request_body = dumps(
        new_time_event.to_dict(), indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.OK

        body = await resp.json()
        assert body["status"] == "Error"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return OK, and a body containing one time_event."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/time-events/{time_event_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == time_event_id
        assert body["event_id"] == time_event.event_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_events_by_event_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_events: list[TimeEvent],
) -> None:
    """Should return OK, and a body containing one time_event."""
    event_id = time_events[0].event_id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=time_events,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/time-events?eventId={event_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["event_id"] == time_events[0].event_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_events_by_event_id_and_bib(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_events: list[TimeEvent],
) -> None:
    """Should return OK, and a body containing one time_event."""
    bib = time_events[0].bib
    event_id = time_events[0].event_id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id_and_bib",
        return_value=[
            time_event for time_event in time_events if time_event.bib == bib
        ],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/time-events?eventId={event_id}&bib={bib}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["event_id"] == time_events[0].event_id
        assert body[0]["bib"] == time_events[0].bib


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_events_by_event_id_and_timing_point(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_events: list[TimeEvent],
) -> None:
    """Should return OK, and a body containing one time_event."""
    event_id = time_events[0].event_id
    timing_point = time_events[0].timing_point
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id_and_timing_point",
        return_value=time_events,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(
            f"/time-events?eventId={event_id}&timingPoint={timing_point}"
        )
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["event_id"] == time_events[0].event_id
        assert body[0]["timing_point"] == time_events[0].timing_point


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_events_by_race_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_events: list[TimeEvent],
) -> None:
    """Should return OK, and a body containing one time_event."""
    race_id = time_events[0].race_id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=time_events,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/time-events?raceId={race_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["race_id"] == time_events[0].race_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return No Content."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(time_event.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"/time-events/{time_event_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_time_events(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return OK and a valid json body."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_all_time_events",
        return_value=[time_event],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.get("/time-events")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        time_events = await resp.json()
        assert type(time_events) is list
        assert len(time_events) > 0
        assert time_events[0]["id"] == time_event_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_time_event_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_event: TimeEvent,
    race_result: RaceResult,
) -> None:
    """Should return No Content."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result.id,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.delete(f"/time-events/{time_event_id}", headers=headers)
        assert resp.status == HTTPStatus.NO_CONTENT


# Bad cases


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    request_body = dumps(time_event.to_dict(), indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_race_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    race: IndividualSprintRace,
    race_result: RaceResult,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 200 OK, and a body containing the new time-event, status=Error."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(f"Race with id {race.id} not found."),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    request_body = dumps(
        new_time_event.to_dict(), indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.OK

        body = await resp.json()
        assert body["status"] == "Error"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_does_not_reference_race(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    race: IndividualSprintRace,
    race_result: RaceResult,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 200 OK, and a body containing the new time-event, status=Error."""
    time_event_id = time_event.id
    time_event_with_no_race_reference = deepcopy(new_time_event)
    time_event_with_no_race_reference.race_id = None
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(f"Race with id {race.id} not found."),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    request_body = dumps(
        time_event_with_no_race_reference.to_dict(),
        indent=4,
        sort_keys=True,
        default=str,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.OK

        body = await resp.json()
        assert body["status"] == "Error"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_is_not_identifiable(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    race: IndividualSprintRace,
    race_result: RaceResult,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 200 OK, and a body containing the new time-event, status=Error."""
    time_event_id = time_event.id
    time_event_with_no_id = deepcopy(new_time_event)
    time_event_with_no_id.id = None
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(f"Race with id {race.id} not found."),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    request_body = dumps(
        time_event_with_no_id.to_dict(), indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.OK

        body = await resp.json()
        assert body["status"] == "Error"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_adapter_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_time_event: TimeEvent,
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    request_body = dumps(
        new_time_event.to_dict(), indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": time_event_id}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post("/time-events", headers=headers, json=request_body)
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_bib_timing_point_exist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    start_entry: StartEntry,
    race: dict,
    race_result: RaceResult,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 400 Bad request."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[time_event],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
    )

    request_body = dumps(
        new_time_event.to_dict(), indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": time_event_id}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"/time-events/{time_event_id}", headers=headers, json=request_body
        )
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    update_body = deepcopy(time_event)
    update_body.id = "different_id"
    request_body = dumps(update_body.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"/time-events/{time_event_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_time_event_by_id_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_event: TimeEvent,
    race_result: RaceResult,
) -> None:
    """Should return 404 Not Found."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result.id,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.delete(f"/time-events/{time_event_id}", headers=headers)
        assert resp.status == HTTPStatus.NOT_FOUND


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_no_authorization(
    client: _TestClient, mocker: MockFixture, new_time_event: TimeEvent
) -> None:
    """Should return 401 Unauthorized."""
    time_event_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    request_body = dumps(
        new_time_event.to_dict(), indent=4, sort_keys=True, default=str
    )
    headers = {hdrs.CONTENT_TYPE: "application/json"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 401 Unauthorized."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    request_body = dumps(time_event.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.put(
            f"/time-events/{time_event_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_time_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 401 Unauthorized."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.delete(f"/time-events/{time_event_id}")
        assert resp.status == HTTPStatus.UNAUTHORIZED


# Forbidden:
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 403 Forbidden."""
    time_event_id = time_event.id
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    request_body = dumps(
        new_time_event.to_dict(), indent=4, sort_keys=True, default=str
    )
    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=403)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.FORBIDDEN


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    time_event_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/time-events/{time_event_id}")
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 404 Not found."""
    time_event_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(time_event.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.put(
            f"/time-events/{time_event_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_time_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    time_event_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.delete(f"/time-events/{time_event_id}", headers=headers)
        assert resp.status == HTTPStatus.NOT_FOUND
