"""Integration test cases for the time_events route."""

import os
import uuid
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from json import dumps
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app.adapters import RaceNotFoundError, TimeEventNotFoundError
from app.models import (
    Changelog,
    IndividualSprintRace,
    RaceResult,
    StartEntry,
    TimeEvent,
)


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {
        "username": os.getenv("ADMIN_USERNAME"),
        "exp": 9999999999,
        "role": "admin",
    }
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"username": "user", "exp": 9999999999, "role": "user"}
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
        id="621461f5-91a2-5f82-99f9-ea72c3278b07",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
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
        id="f910dc1f-18da-50b1-948b-c847165a0556",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=0,
        max_no_of_contestants=10,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=["621461f5-91a2-5f82-99f9-ea72c3278b07"],
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
        id="50b75bea-866a-50fc-bde0-78cc68b04fec",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
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
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        timing_point="Finish",
        rank=0,
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        next_race="semi_name1",
        next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
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
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        timing_point="Finish",
        rank=0,
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        next_race="semi_name1",
        next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
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
            event_id="e726010d-728b-5516-a930-dd8e9b210255",
            name="Petter Propell",
            club="Barnehagen",
            race="race_name",
            race_id="f910dc1f-18da-50b1-948b-c847165a0556",
            timing_point="Finish",
            rank=0,
            registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
            next_race="semi_name1",
            next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
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
    client: TestClient,
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
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=lambda id_: time_event.model_copy(update={"id": id_}),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
    )

    request_body = dumps(
        new_time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/time-events", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.OK

    body = resp.json()
    assert body["status"] == "OK"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_race_result_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    start_entry: StartEntry,
    race: dict,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 200 OK, and a body containing the new time-event."""
    time_event_id = time_event.id
    race_result_id = "65b04195-4e72-5d21-a0eb-1597fa819e96"
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.create_race_result",
        return_value=race_result_id,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=lambda id_: time_event.model_copy(update={"id": id_}),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
    )

    request_body = dumps(
        new_time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/time-events", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.OK

    body = resp.json()
    assert body["status"] == "OK"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_contestant_not_in_race(
    client: TestClient,
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
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=lambda id_: time_event.model_copy(update={"id": id_}),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_wrong_bib],
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    request_body = dumps(
        new_time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/time-events", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.OK

    body = resp.json()
    assert body["status"] == "Error"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_event_by_id(
    client: TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return OK, and a body containing one time_event."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )

    resp = client.get(f"/time-events/{time_event_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(time_event_id)
    assert body["event_id"] == str(time_event.event_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_events_by_event_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_events: list[TimeEvent],
) -> None:
    """Should return OK, and a body containing one time_event."""
    event_id = time_events[0].event_id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=time_events,
    )

    resp = client.get(f"/time-events?eventId={event_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["event_id"] == str(time_events[0].event_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_events_by_event_id_and_bib(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_events: list[TimeEvent],
) -> None:
    """Should return OK, and a body containing one time_event."""
    bib = time_events[0].bib
    event_id = time_events[0].event_id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id_and_bib",
        return_value=[
            time_event for time_event in time_events if time_event.bib == bib
        ],
    )

    resp = client.get(f"/time-events?eventId={event_id}&bib={bib}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["event_id"] == str(time_events[0].event_id)
    assert body[0]["bib"] == time_events[0].bib


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_events_by_event_id_and_timing_point(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_events: list[TimeEvent],
) -> None:
    """Should return OK, and a body containing one time_event."""
    event_id = time_events[0].event_id
    timing_point = time_events[0].timing_point
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id_and_timing_point",
        return_value=time_events,
    )

    resp = client.get(f"/time-events?eventId={event_id}&timingPoint={timing_point}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["event_id"] == str(time_events[0].event_id)
    assert body[0]["timing_point"] == time_events[0].timing_point


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_events_by_race_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_events: list[TimeEvent],
) -> None:
    """Should return OK, and a body containing one time_event."""
    race_id = time_events[0].race_id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=time_events,
    )

    resp = client.get(f"/time-events?raceId={race_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["race_id"] == str(time_events[0].race_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_by_id(
    client: TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return No Content."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"/time-events/{time_event_id}", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_time_events(
    client: TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return OK and a valid json body."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_all_time_events",
        return_value=[time_event],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    resp = client.get("/time-events")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    time_events = resp.json()
    assert type(time_events) is list
    assert len(time_events) > 0
    assert time_events[0]["id"] == str(time_event_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_time_event_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_event: TimeEvent,
    race_result: RaceResult,
) -> None:
    """Should return No Content."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result.id,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/time-events/{time_event_id}", headers=headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT


# Bad cases


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_race_not_found(
    client: TestClient,
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
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(f"Race with id {race.id} not found."),
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=lambda id_: time_event.model_copy(update={"id": id_}),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    request_body = dumps(
        new_time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/time-events", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.OK

    body = resp.json()
    assert body["status"] == "Error"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_does_not_reference_race(
    client: TestClient,
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
        "app.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(f"Race with id {race.id} not found."),
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=lambda id_: time_event.model_copy(update={"id": id_}),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )

    request_body = dumps(
        time_event_with_no_race_reference.model_dump(mode="json"),
        indent=4,
        sort_keys=True,
        default=str,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/time-events", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.OK

    body = resp.json()
    assert body["status"] == "Error"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_adapter_fails(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_time_event: TimeEvent,
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    request_body = dumps(
        new_time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/time-events", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_mandatory_property(
    client: TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=lambda id_: time_event.model_copy(update={"id": id_}),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = {"id": str(time_event_id)}

    resp = client.post("/time-events", headers=headers, json=request_body)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_bib_timing_point_exist(
    client: TestClient,
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
        "app.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[time_event],
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=lambda id_: time_event.model_copy(update={"id": id_}),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
    )

    request_body = dumps(
        new_time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/time-events", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_by_id_missing_mandatory_property(
    client: TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = {"id": str(time_event_id)}

    resp = client.put(
        f"/time-events/{time_event_id}", headers=headers, json=request_body
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_by_id_different_id_in_body(
    client: TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    update_body = deepcopy(time_event)
    update_body.id = uuid.UUID("2b920f5c-eb82-5655-bd13-2001e5f0683e")
    request_body = dumps(
        update_body.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"/time-events/{time_event_id}", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_time_event_by_id_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    time_event: TimeEvent,
    race_result: RaceResult,
) -> None:
    """Should return 404 Not Found."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result.id,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/time-events/{time_event_id}", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_no_authorization(
    client: TestClient, mocker: MockFixture, new_time_event: TimeEvent
) -> None:
    """Should return 401 Unauthorized."""
    time_event_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    request_body = dumps(
        new_time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )
    headers = {"Content-Type": "application/json"}

    resp = client.post("/time-events", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 401 Unauthorized."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {"Content-Type": "application/json"}

    request_body = dumps(
        time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"/time-events/{time_event_id}", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_time_event_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 401 Unauthorized."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    resp = client.delete(f"/time-events/{time_event_id}")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


# Forbidden:
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_time_event_insufficient_role(
    client: TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    new_time_event: TimeEvent,
    time_event: TimeEvent,
) -> None:
    """Should return 403 Forbidden."""
    time_event_id = time_event.id
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=time_event_id,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    request_body = dumps(
        new_time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token_unsufficient_role}",
    }

    resp = client.post("/time-events", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.FORBIDDEN


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_time_event_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    time_event_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    resp = client.get(f"/time-events/{time_event_id}")
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_time_event_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture, time_event: TimeEvent
) -> None:
    """Should return 404 Not found."""
    time_event_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        time_event.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"/time-events/{time_event_id}", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_time_event_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    time_event_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=TimeEventNotFoundError(
            f"TimeEvent with id {id} not found in database."
        ),
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=[],
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/time-events/{time_event_id}", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND
