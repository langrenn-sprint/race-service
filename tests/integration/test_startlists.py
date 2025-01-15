"""Integration test cases for the startlists route."""

import os
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

from race_service.adapters import StartlistNotFoundError
from race_service.models import IntervalStartRace, StartEntry, Startlist

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


RACES: list[IntervalStartRace] = [
    IntervalStartRace(
        id="race_1",
        raceclass="J15",
        order=1,
        event_id="event_1",
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=2,
        max_no_of_contestants=10,
        raceplan_id="raceplan_1",
        start_entries=["11", "22"],
        results={},
        datatype="interval_start",
    ),
    IntervalStartRace(
        id="race_2",
        raceclass="G15",
        order=2,
        event_id="event_1",
        max_no_of_contestants=10,
        start_time=datetime.fromisoformat("2021-08-31T12:01:00"),
        no_of_contestants=2,
        raceplan_id="raceplan_1",
        start_entries=[
            "33",
            "44",
        ],
        results={},
        datatype="interval_start",
    ),
    IntervalStartRace(
        id="race_3",
        raceclass="G16",
        order=3,
        event_id="event_1",
        max_no_of_contestants=10,
        start_time=datetime.fromisoformat("2021-08-31T12:02:00"),
        no_of_contestants=2,
        raceplan_id="raceplan_1",
        start_entries=["55", "66"],
        results={},
        datatype="interval_start",
    ),
    IntervalStartRace(
        id="race_4",
        raceclass="J16",
        order=4,
        event_id="event_1",
        max_no_of_contestants=10,
        start_time=datetime.fromisoformat("2021-08-31T12:03:00"),
        no_of_contestants=2,
        raceplan_id="raceplan_1",
        start_entries=["77", "88"],
        results={},
        datatype="interval_start",
    ),
]


@pytest.fixture
async def races() -> list[IntervalStartRace]:
    """Create a mock race object."""
    return RACES


def get_race_by_id(db: Any, id_: str) -> IntervalStartRace:
    """Mock function to look up correct race from list."""
    return next(race for race in RACES if race.id == id_)


START_ENTRIES: list[StartEntry] = [
    StartEntry(
        id="11",
        race_id="J15",
        bib=1,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:00:00"),
        starting_position=1,
        startlist_id="startlist_1",
    ),
    StartEntry(
        id="22",
        race_id="J15",
        bib=2,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:00:30"),
        starting_position=2,
        startlist_id="startlist_1",
    ),
    StartEntry(
        id="33",
        race_id="G15",
        bib=3,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:01:00"),
        starting_position=1,
        startlist_id="startlist_1",
    ),
    StartEntry(
        id="44",
        race_id="G15",
        bib=4,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:01:30"),
        starting_position=2,
        startlist_id="startlist_1",
    ),
    StartEntry(
        id="55",
        race_id="J16",
        bib=5,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:02:00"),
        starting_position=1,
        startlist_id="startlist_1",
    ),
    StartEntry(
        id="66",
        race_id="J16",
        bib=6,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:02:30"),
        starting_position=2,
        startlist_id="startlist_1",
    ),
    StartEntry(
        id="77",
        race_id="G16",
        bib=7,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:03:00"),
        starting_position=1,
        startlist_id="startlist_1",
    ),
    StartEntry(
        id="88",
        race_id="G16",
        bib=8,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:03:30"),
        starting_position=2,
        startlist_id="startlist_1",
    ),
]


@pytest.fixture
async def start_entries() -> list[StartEntry]:
    """Create a mock startlist object."""
    return START_ENTRIES


def get_start_entry_by_id(db: Any, id_: str) -> StartEntry:
    """Mock function to look up correct race from list."""
    return next(start_entry for start_entry in START_ENTRIES if start_entry.id == id_)


@pytest.fixture
async def new_startlist(start_entries: list[StartEntry]) -> Startlist:
    """Create a startlist object."""
    return Startlist(
        event_id="event_1",
        no_of_contestants=8,
        start_entries=[
            start_entry.id for start_entry in start_entries if start_entry.id
        ],
    )


@pytest.fixture
async def startlist(start_entries: list[StartEntry]) -> Startlist:
    """Create a mock startlist object."""
    return Startlist(
        id="startlist_1",
        event_id="event_1",
        no_of_contestants=8,
        start_entries=[
            start_entry.id for start_entry in start_entries if start_entry.id
        ],
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_startlist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_startlist: Startlist,
    startlist: Startlist,
) -> None:
    """Should return 405 Method Not Allowed."""
    startlist_id = startlist.id
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=startlist_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=startlist_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    request_body = dumps(new_startlist, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/startlists", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_startlist_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    startlist: Startlist,
) -> None:
    """Should return OK, and a body containing one startlist."""
    startlist_id = startlist.id
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/startlists/{startlist_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == startlist_id
        assert body["event_id"] == startlist.event_id
        assert len(body["start_entries"]) == len(startlist.start_entries)
        for start_entry in body["start_entries"]:
            assert start_entry["race_id"]
            assert start_entry["bib"]
            assert start_entry["starting_position"]
            assert start_entry["scheduled_start_time"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_startlists_by_event_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    startlist: Startlist,
) -> None:
    """Should return OK, and a body containing one startlist."""
    event_id = startlist.event_id
    startlist_id = startlist.id
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[startlist],
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/startlists?eventId={event_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == startlist_id
        assert body[0]["event_id"] == startlist.event_id
        assert len(body[0]["start_entries"]) == len(startlist.start_entries)
        for start_entry in body[0]["start_entries"]:
            assert start_entry["race_id"]
            assert start_entry["bib"]
            assert start_entry["starting_position"]
            assert start_entry["scheduled_start_time"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_startlists_by_event_id_and_bib(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    startlist: Startlist,
) -> None:
    """Should return OK, and a body containing one startlist with start_entries where bib == bib."""
    event_id = startlist.event_id
    startlist_id = startlist.id
    bib = START_ENTRIES[0].bib
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[startlist],
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/startlists?eventId={event_id}&bib={bib}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == startlist_id
        assert body[0]["event_id"] == startlist.event_id
        assert len(body[0]["start_entries"]) == len(
            [se for se in START_ENTRIES if se.bib == bib]
        )
        for start_entry in body[0]["start_entries"]:
            assert start_entry["race_id"]
            assert start_entry["bib"] == bib
            assert start_entry["starting_position"]
            assert start_entry["scheduled_start_time"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_startlist_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: Startlist
) -> None:
    """Should return 405 Method not allowed."""
    startlist_id = startlist.id
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=startlist_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(startlist, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"/startlists/{startlist_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_startlists(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: Startlist
) -> None:
    """Should return OK and a valid json body."""
    startlist_id = startlist.id
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_all_startlists",
        return_value=[startlist],
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.get("/startlists")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        startlists = await resp.json()
        assert type(startlists) is list
        assert len(startlists) > 0
        assert startlists[0]["id"] == startlist_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_startlist_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    start_entries: list[dict],
    startlist: Startlist,
    races: list[dict],
) -> None:
    """Should return No Content."""
    startlist_id = startlist.id
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=startlist_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=start_entries,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=races,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=get_race_by_id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.delete(f"/startlists/{startlist_id}", headers=headers)
        assert resp.status == HTTPStatus.NO_CONTENT


# Bad cases


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_startlist_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, startlist: Startlist
) -> None:
    """Should return 401 Unauthorized."""
    startlist_id = startlist.id
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=startlist_id,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.delete(f"/startlists/{startlist_id}")
        assert resp.status == HTTPStatus.UNAUTHORIZED


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_startlist_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    startlist_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/startlists/{startlist_id}")
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_startlist_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    startlist_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.delete(f"/startlists/{startlist_id}", headers=headers)
        assert resp.status == HTTPStatus.NOT_FOUND
