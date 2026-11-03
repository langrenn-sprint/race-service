"""Integration test cases for the startlists route."""

import os
from datetime import datetime
from http import HTTPStatus
from json import dumps

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app.adapters import StartlistNotFoundError
from app.models import IntervalStartRace, StartEntry, Startlist


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


RACES: list[IntervalStartRace] = [
    IntervalStartRace(
        id="f910dc1f-18da-50b1-948b-c847165a0556",
        raceclass="J15",
        order=1,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=2,
        max_no_of_contestants=10,
        raceplan_id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
        start_entries=[
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
        ],
        results={},
        datatype="interval_start",
    ),
    IntervalStartRace(
        id="fa9e1174-f861-5300-a867-1cc364621b5c",
        raceclass="G15",
        order=2,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        max_no_of_contestants=10,
        start_time=datetime.fromisoformat("2021-08-31T12:01:00"),
        no_of_contestants=2,
        raceplan_id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
        start_entries=[
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
        ],
        results={},
        datatype="interval_start",
    ),
    IntervalStartRace(
        id="e222b1af-b820-5165-a2ad-ae76db9c9456",
        raceclass="G16",
        order=3,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        max_no_of_contestants=10,
        start_time=datetime.fromisoformat("2021-08-31T12:02:00"),
        no_of_contestants=2,
        raceplan_id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
        start_entries=[
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
        ],
        results={},
        datatype="interval_start",
    ),
    IntervalStartRace(
        id="551c94af-eb9d-58b5-99d6-02299bd6e363",
        raceclass="J16",
        order=4,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        max_no_of_contestants=10,
        start_time=datetime.fromisoformat("2021-08-31T12:03:00"),
        no_of_contestants=2,
        raceplan_id="b24f50bf-52e0-589a-a8cc-2bee6f7a4b64",
        start_entries=[
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
        results={},
        datatype="interval_start",
    ),
]


@pytest.fixture
async def races() -> list[IntervalStartRace]:
    """Create a mock race object."""
    return RACES


def get_race_by_id(id_: str) -> IntervalStartRace:
    """Mock function to look up correct race from list."""
    return next(race for race in RACES if str(race.id) == str(id_))


START_ENTRIES: list[StartEntry] = [
    StartEntry(
        id="f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
        race_id="49c6bdfd-0728-56e0-ba1c-a30f12b6f5a9",
        bib=1,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:00:00"),
        starting_position=1,
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
    ),
    StartEntry(
        id="5152cfad-4307-565b-8e66-e81f02d8d4e3",
        race_id="49c6bdfd-0728-56e0-ba1c-a30f12b6f5a9",
        bib=2,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:00:30"),
        starting_position=2,
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
    ),
    StartEntry(
        id="1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
        race_id="68514d16-4b9d-519e-bdae-9f2907c4b2f2",
        bib=3,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:01:00"),
        starting_position=1,
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
    ),
    StartEntry(
        id="7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
        race_id="68514d16-4b9d-519e-bdae-9f2907c4b2f2",
        bib=4,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:01:30"),
        starting_position=2,
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
    ),
    StartEntry(
        id="91547337-a276-5407-962e-a591c95b0478",
        race_id="20f36d68-ef6d-5b75-933c-e4d313333a1c",
        bib=5,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:02:00"),
        starting_position=1,
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
    ),
    StartEntry(
        id="35106e04-9f97-5e62-a112-fbfd7cc6924b",
        race_id="20f36d68-ef6d-5b75-933c-e4d313333a1c",
        bib=6,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:02:30"),
        starting_position=2,
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
    ),
    StartEntry(
        id="de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
        race_id="9ae36c7b-4251-538f-b440-7ffeb23b8e1e",
        bib=7,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:03:00"),
        starting_position=1,
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
    ),
    StartEntry(
        id="6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        race_id="9ae36c7b-4251-538f-b440-7ffeb23b8e1e",
        bib=8,
        name="name names",
        club="the club",
        scheduled_start_time=datetime.fromisoformat("2021-08-31 12:03:30"),
        starting_position=2,
        startlist_id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
    ),
]


@pytest.fixture
async def start_entries() -> list[StartEntry]:
    """Create a mock startlist object."""
    return START_ENTRIES


def get_start_entry_by_id(id_: str) -> StartEntry:
    """Mock function to look up correct race from list."""
    return next(
        start_entry for start_entry in START_ENTRIES if str(start_entry.id) == str(id_)
    )


@pytest.fixture
async def new_startlist(start_entries: list[StartEntry]) -> Startlist:
    """Create a startlist object."""
    return Startlist(
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        no_of_contestants=8,
        start_entries=[
            start_entry.id for start_entry in start_entries if start_entry.id
        ],
    )


@pytest.fixture
async def startlist(start_entries: list[StartEntry]) -> Startlist:
    """Create a mock startlist object."""
    return Startlist(
        id="1aee97da-ab22-51fc-a615-ec53f7aa33d7",
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        no_of_contestants=8,
        start_entries=[
            start_entry.id for start_entry in start_entries if start_entry.id
        ],
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_startlist(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_startlist: Startlist,
    startlist: Startlist,
) -> None:
    """Should return 405 Method Not Allowed."""
    startlist_id = startlist.id
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=startlist_id,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    request_body = dumps(new_startlist, indent=4, sort_keys=True, default=str)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("/startlists", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_startlist_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    startlist: Startlist,
) -> None:
    """Should return OK, and a body containing one startlist."""
    startlist_id = startlist.id
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )

    resp = client.get(f"/startlists/{startlist_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(startlist_id)
    assert body["event_id"] == str(startlist.event_id)
    assert len(body["start_entries"]) == len(startlist.start_entries)
    for start_entry in body["start_entries"]:
        assert start_entry["race_id"]
        assert start_entry["bib"]
        assert start_entry["starting_position"]
        assert start_entry["scheduled_start_time"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_startlists_by_event_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    startlist: Startlist,
) -> None:
    """Should return OK, and a body containing one startlist."""
    event_id = startlist.event_id
    startlist_id = startlist.id
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[startlist],
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )

    resp = client.get(f"/startlists?eventId={event_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["id"] == str(startlist_id)
    assert body[0]["event_id"] == str(startlist.event_id)
    assert len(body[0]["start_entries"]) == len(startlist.start_entries)
    for start_entry in body[0]["start_entries"]:
        assert start_entry["race_id"]
        assert start_entry["bib"]
        assert start_entry["starting_position"]
        assert start_entry["scheduled_start_time"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_startlists_by_event_id_and_bib(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    startlist: Startlist,
) -> None:
    """Should return OK, and a body containing one startlist with start_entries where bib == bib."""
    event_id = startlist.event_id
    startlist_id = startlist.id
    bib = START_ENTRIES[0].bib
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[startlist],
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )

    resp = client.get(f"/startlists?eventId={event_id}&bib={bib}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is list
    assert len(body) == 1
    assert body[0]["id"] == str(startlist_id)
    assert body[0]["event_id"] == str(startlist.event_id)
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
    client: TestClient, mocker: MockFixture, token: MockFixture, startlist: Startlist
) -> None:
    """Should return 405 Method not allowed."""
    startlist_id = startlist.id
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=startlist_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(startlist, indent=4, sort_keys=True, default=str)

    resp = client.put(
        f"/startlists/{startlist_id}", headers=headers, content=request_body
    )
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_startlists(
    client: TestClient, mocker: MockFixture, token: MockFixture, startlist: Startlist
) -> None:
    """Should return OK and a valid json body."""
    startlist_id = startlist.id
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_all_startlists",
        return_value=[startlist],
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    resp = client.get("/startlists")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    startlists = resp.json()
    assert type(startlists) is list
    assert len(startlists) > 0
    assert startlists[0]["id"] == str(startlist_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_startlist_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    start_entries: list[dict],
    startlist: Startlist,
    races: list[dict],
) -> None:
    """Should return No Content."""
    startlist_id = startlist.id
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=startlist_id,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=start_entries,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )
    mocker.patch(
        "app.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=races,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=get_race_by_id,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/startlists/{startlist_id}", headers=headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT


# Bad cases


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_startlist_by_id_no_authorization(
    client: TestClient, mocker: MockFixture, startlist: Startlist
) -> None:
    """Should return 401 Unauthorized."""
    startlist_id = startlist.id
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=startlist_id,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    resp = client.delete(f"/startlists/{startlist_id}")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_startlist_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    startlist_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    resp = client.get(f"/startlists/{startlist_id}")
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_startlist_not_found(
    client: TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    startlist_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        side_effect=StartlistNotFoundError(f"Startlist with id {id} not found."),
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=None,
    )
    mocker.patch(
        "app.adapters.startlists_adapter.StartlistsAdapter.get_startlists_by_event_id",
        return_value=[],
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/startlists/{startlist_id}", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND
