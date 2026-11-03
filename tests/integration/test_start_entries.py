"""Integration test cases for the start_entries route."""

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

from app.adapters import (
    RaceNotFoundError,
    StartEntryNotFoundError,
    StartlistNotFoundError,
)
from app.models import IndividualSprintRace, Raceplan, StartEntry, Startlist


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
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def competition_format() -> dict[str, Any]:
    """A competition-format for testing."""
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
        "race_config_ranked": None,
    }


@pytest.fixture
async def race() -> IndividualSprintRace:
    """Create a mock race object."""
    return IndividualSprintRace(
        id="f910dc1f-18da-50b1-948b-c847165a0556",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[],
        results={},
        round="Q",
        index="",
        heat=1,
        rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
        datatype="individual_sprint",
    )


@pytest.fixture
async def startlist(event: dict) -> Startlist:
    """Create a startlist object."""
    return Startlist(
        id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
        event_id=event["id"],
        no_of_contestants=0,
        start_entries=[],
    )


@pytest.fixture
async def new_start_entry() -> StartEntry:
    """Create a start_entry object."""
    return StartEntry(
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
        bib=1,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        starting_position=1,
    )


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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_start_entry(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    race: IndividualSprintRace,
    startlist: Startlist,
    new_start_entry: StartEntry,
    start_entry: StartEntry,
    competition_format: dict,
) -> None:
    """Should return Created, location header."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=StartEntryNotFoundError("Start-entry not found."),
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=start_entry_id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
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
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=Raceplan(
            id="1bc606b2-a8bf-5870-a468-af93bd62e7c0",
            event_id=event["id"],
            races=[],
            no_of_contestants=0,
        ),
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    request_body = dumps(
        new_start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"races/{race.id}/start-entries", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.CREATED
    assert f"races/{race.id}/start-entries/" in resp.headers["Location"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_start_entry_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
) -> None:
    """Should return OK, and a body containing one start_entry."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )

    resp = client.get(f"races/{race.id}/start-entries/{start_entry_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(start_entry_id)
    assert body["startlist_id"] == str(start_entry.startlist_id)
    assert body["race_id"] == str(start_entry.race_id)
    assert body["bib"] == start_entry.bib
    assert body["starting_position"] == start_entry.starting_position
    assert body["scheduled_start_time"] == datetime.isoformat(
        start_entry.scheduled_start_time
    )
    assert body["name"] == start_entry.name
    assert body["club"] == start_entry.club
    assert body["status"] == start_entry.status
    assert body["changelog"] == start_entry.changelog


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_start_entry_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
) -> None:
    """Should return No Content."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=start_entry_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"races/{race.id}/start-entries/{start_entry_id}",
        headers=headers,
        content=request_body,
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_start_entries_by_race_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
) -> None:
    """Should return OK and a valid json body."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
    )

    resp = client.get(f"races/{race.id}/start-entries")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    start_entries = resp.json()
    assert type(start_entries) is list
    assert len(start_entries) > 0
    assert start_entries[0]["id"] == str(start_entry_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_start_entries_by_race_id_and_startlist_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    startlist: Startlist,
    start_entry: StartEntry,
) -> None:
    """Should return OK and a valid json body."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id_and_startlist_id",
        return_value=[start_entry],
    )

    resp = client.get(f"races/{race.id}/start-entries?startlistId={startlist.id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    start_entries = resp.json()
    assert type(start_entries) is list
    assert len(start_entries) > 0
    assert start_entries[0]["id"] == str(start_entry_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_start_entry(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    race: IndividualSprintRace,
    startlist: Startlist,
    start_entry: StartEntry,
    competition_format: dict,
) -> None:
    """Should return No Content."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
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
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=Raceplan(
            id="1bc606b2-a8bf-5870-a468-af93bd62e7c0",
            event_id=event["id"],
            races=[],
            no_of_contestants=0,
        ),
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(
        f"races/{race.id}/start-entries/{start_entry_id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT


# Bad cases


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_start_entry_race_is_full(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    race: IndividualSprintRace,
    startlist: Startlist,
    new_start_entry: StartEntry,
    start_entry: StartEntry,
) -> None:
    """Should return 400 Bad request."""
    start_entry_id = start_entry.id
    full_race = deepcopy(race)
    full_race.start_entries = [f"{s}" for s in range(1, race.max_no_of_contestants + 1)]
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=start_entry_id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=full_race,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(
        new_start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"races/{race.id}/start-entries", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_start_entry_race_bib_already_in_race(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    startlist: Startlist,
    new_start_entry: StartEntry,
    start_entry: StartEntry,
) -> None:
    """Should return 400 Bad request."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=start_entry_id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
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
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(
        new_start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"races/{race.id}/start-entries", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_start_entry_race_position_is_taken(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    startlist: Startlist,
    new_start_entry: StartEntry,
    start_entry: StartEntry,
) -> None:
    """Should return 400 Bad request."""
    start_entry_id = start_entry.id
    start_entry_different_bib_same_starting_position = deepcopy(start_entry)
    start_entry_different_bib_same_starting_position.bib = 1000
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=start_entry_id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_different_bib_same_starting_position],
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
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(
        new_start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"races/{race.id}/start-entries", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_start_entry_adapter_fails(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
    startlist: Startlist,
    new_start_entry: StartEntry,
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=StartEntryNotFoundError("Start-entry not found."),
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
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
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(
        new_start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"races/{race.id}/start-entries", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_start_entry_mandatory_property(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
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
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = {"id": str(start_entry_id)}

    resp = client.post(
        f"races/{race.id}/start-entries", headers=headers, json=request_body
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_start_entry_by_id_missing_mandatory_property(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=start_entry_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = {"id": str(start_entry_id)}

    resp = client.put(
        f"races/{race.id}/start-entries/{start_entry_id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_start_entry_by_id_different_id_in_body(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=start_entry_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    update_body = deepcopy(start_entry)
    update_body.id = uuid.UUID("2b920f5c-eb82-5655-bd13-2001e5f0683e")
    request_body = dumps(
        update_body.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"races/{race.id}/start-entries/{start_entry_id}",
        headers=headers,
        content=request_body,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_start_entry_race_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    startlist: Startlist,
    start_entry: StartEntry,
    competition_format: dict,
) -> None:
    """Should return 404 Not found."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
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
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(
        f"races/{race.id}/start-entries/{start_entry_id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND
    body = resp.json()
    assert "DB is inconsistent: cannot find race with id" in body["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_start_entry_startlist_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    race: IndividualSprintRace,
    startlist: Startlist,
    start_entry: StartEntry,
    competition_format: dict,
) -> None:
    """Should return 404 Not found."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
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
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=Raceplan(
            id="1bc606b2-a8bf-5870-a468-af93bd62e7c0",
            event_id=event["id"],
            races=[],
            no_of_contestants=0,
        ),
    )
    mocker.patch(
        "app.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(
        f"races/{race.id}/start-entries/{start_entry_id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND
    body = resp.json()
    assert "DB is inconsistent: cannot find startlist with id" in body["detail"]


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_start_entry_no_authorization(
    client: TestClient,
    mocker: MockFixture,
    race: IndividualSprintRace,
    new_start_entry: StartEntry,
) -> None:
    """Should return 401 Unauthorized."""
    start_entry_id = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=start_entry_id,
    )

    request_body = dumps(
        new_start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {"Content-Type": "application/json"}

    resp = client.post(
        f"races/{race.id}/start-entries", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_start_entry_by_id_no_authorization(
    client: TestClient,
    mocker: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
) -> None:
    """Should return 401 Unauthorized."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=start_entry_id,
    )

    headers = {"Content-Type": "application/json"}

    request_body = dumps(
        start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"races/{race.id}/start-entries/{start_entry_id}",
        headers=headers,
        content=request_body,
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_start_entry_by_id_no_authorization(
    client: TestClient,
    mocker: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
) -> None:
    """Should return 401 Unauthorized."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=StartEntryNotFoundError(f"StartEntry with id {id} not found"),
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=start_entry_id,
    )

    resp = client.delete(f"races/{race.id}/start-entries/{start_entry_id}")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


# Forbidden:
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_start_entry_insufficient_role(
    client: TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    race: IndividualSprintRace,
    new_start_entry: StartEntry,
    start_entry: StartEntry,
) -> None:
    """Should return 403 Forbidden."""
    start_entry_id = start_entry.id
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=start_entry_id,
    )

    request_body = dumps(
        new_start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token_unsufficient_role}",
    }

    resp = client.post(
        f"races/{race.id}/start-entries", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_start_entry_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
) -> None:
    """Should return 404 Not found."""
    start_entry_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=StartEntryNotFoundError(f"StartEntry with id {id} not found"),
    )

    resp = client.get(f"races/{race.id}/start-entries/{start_entry_id}")
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_start_entry_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    start_entry: StartEntry,
) -> None:
    """Should return 404 Not found."""
    start_entry_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=StartEntryNotFoundError(f"StartEntry with id {id} not found"),
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        start_entry.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"races/{race.id}/start-entries/{start_entry_id}",
        headers=headers,
        content=request_body,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_start_entry_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
) -> None:
    """Should return 404 Not found."""
    start_entry_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=StartEntryNotFoundError(f"StartEntry with id {id} not found"),
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=None,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(
        f"races/{race.id}/start-entries/{start_entry_id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
async def test_create_start_entry_id_already_exists(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    startlist: Startlist,
    new_start_entry: StartEntry,
    start_entry: StartEntry,
) -> None:
    """Should return 422 Unprocessable Entity when the given id is already in use."""
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    create_start_entry = mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=start_entry.id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )

    request_body = new_start_entry.model_dump(mode="json")
    request_body["id"] = str(start_entry.id)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post(
        f"races/{race.id}/start-entries", headers=headers, json=request_body
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "already exists" in resp.json()["detail"]
    create_start_entry.assert_not_called()
