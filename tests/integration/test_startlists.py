"""Integration test cases for the startlists route."""
from datetime import datetime
from json import dumps
import os
from typing import Any, Dict, List

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
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "user", "roles": ["user"]}
    return jwt.encode(payload, secret, algorithm)  # type: ignore


@pytest.fixture
async def new_startlist() -> dict:
    """Create a startlist object."""
    return {
        "event_id": "event_1",
        "no_of_contestants": 8,
        "start_entries": [
            {
                "race_id": "J15",
                "bib": 1,
                "name": "name names",
                "club": "the club",
                "scheduled_start_time": "2021-08-31T12:00:00",
                "starting_position": 1,
                "id": None,
            },
            {
                "race_id": "J15",
                "bib": 2,
                "name": "name names",
                "club": "the club",
                "scheduled_start_time": "2021-08-31T12:00:30",
                "starting_position": 2,
                "id": None,
            },
            {
                "race_id": "G15",
                "bib": 3,
                "name": "name names",
                "club": "the club",
                "scheduled_start_time": "2021-08-31T12:01:00",
                "starting_position": 1,
                "id": None,
            },
            {
                "race_id": "G15",
                "bib": 4,
                "name": "name names",
                "club": "the club",
                "scheduled_start_time": "2021-08-31T12:01:30",
                "starting_position": 2,
                "id": None,
            },
            {
                "race_id": "J16",
                "bib": 5,
                "name": "name names",
                "club": "the club",
                "scheduled_start_time": "2021-08-31T12:02:00",
                "starting_position": 1,
                "id": None,
            },
            {
                "race_id": "J16",
                "bib": 6,
                "name": "name names",
                "club": "the club",
                "scheduled_start_time": "2021-08-31T12:02:30",
                "starting_position": 2,
                "id": None,
            },
            {
                "race_id": "G16",
                "bib": 7,
                "name": "name names",
                "club": "the club",
                "scheduled_start_time": "2021-08-31T12:03:00",
                "starting_position": 1,
                "id": None,
            },
            {
                "race_id": "G16",
                "bib": 8,
                "name": "name names",
                "club": "the club",
                "scheduled_start_time": "2021-08-31T12:03:30",
                "starting_position": 2,
                "id": None,
            },
        ],
    }


@pytest.fixture
async def startlist() -> dict:
    """Create a mock startlist object."""
    return {
        "id": "startlist_1",
        "event_id": "event_1",
        "no_of_contestants": 8,
        "start_entries": ["11", "22", "33", "44", "55", "66", "77", "88"],
    }


RACES: List[Dict] = [
    {
        "id": "race_1",
        "raceclass": "J15",
        "order": 1,
        "event_id": "event_1",
        "no_of_contestants": 2,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 2,
        "max_no_of_contestants": 10,
        "raceplan_id": "raceplan_1",
        "start_entries": ["11", "22"],
        "results": {},
        "datatype": "interval_start",
    },
    {
        "id": "race_2",
        "raceclass": "G15",
        "order": 2,
        "event_id": "event_1",
        "no_of_contestants": 2,
        "max_no_of_contestants": 10,
        "start_time": "2021-08-31T12:01:00",
        "no_of_contestants": 2,
        "raceplan_id": "raceplan_1",
        "start_entries": [
            "33",
            "44",
        ],
        "results": {},
        "datatype": "interval_start",
    },
    {
        "id": "race_3",
        "raceclass": "G16",
        "order": 3,
        "event_id": "event_1",
        "no_of_contestants": 2,
        "max_no_of_contestants": 10,
        "start_time": "2021-08-31T12:02:00",
        "no_of_contestants": 2,
        "raceplan_id": "raceplan_1",
        "start_entries": ["55", "66"],
        "results": {},
        "datatype": "interval_start",
    },
    {
        "id": "race_4",
        "raceclass": "J16",
        "order": 4,
        "event_id": "event_1",
        "no_of_contestants": 2,
        "max_no_of_contestants": 10,
        "start_time": "2021-08-31T12:03:00",
        "no_of_contestants": 2,
        "raceplan_id": "raceplan_1",
        "start_entries": ["77", "88"],
        "results": {},
        "datatype": "interval_start",
    },
]


@pytest.fixture
async def races() -> List[Dict]:
    """Create a mock race object."""
    return RACES


def get_race_by_id(db: Any, id: str) -> dict:
    """Mock function to look up correct race from list."""
    return next(race for race in RACES if race["id"] == id)


START_ENTRIES: List[Dict] = [
    {
        "id": "11",
        "race_id": "J15",
        "bib": 1,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:00:00"),
        "starting_position": 1,
        "startlist_id": "startlist_1",
    },
    {
        "id": "22",
        "race_id": "J15",
        "bib": 2,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:00:30"),
        "starting_position": 2,
        "startlist_id": "startlist_1",
    },
    {
        "id": "33",
        "race_id": "G15",
        "bib": 3,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:01:00"),
        "starting_position": 1,
        "startlist_id": "startlist_1",
    },
    {
        "id": "44",
        "race_id": "G15",
        "bib": 4,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:01:30"),
        "starting_position": 2,
        "startlist_id": "startlist_1",
    },
    {
        "id": "55",
        "race_id": "J16",
        "bib": 5,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:02:00"),
        "starting_position": 1,
        "startlist_id": "startlist_1",
    },
    {
        "id": "66",
        "race_id": "J16",
        "bib": 6,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:02:30"),
        "starting_position": 2,
        "startlist_id": "startlist_1",
    },
    {
        "id": "77",
        "race_id": "G16",
        "bib": 7,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:03:00"),
        "starting_position": 1,
        "startlist_id": "startlist_1",
    },
    {
        "id": "88",
        "race_id": "G16",
        "bib": 8,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:03:30"),
        "starting_position": 2,
        "startlist_id": "startlist_1",
    },
]


@pytest.fixture
async def start_entries() -> List[Dict]:
    """Create a mock startlist object."""
    return START_ENTRIES


def get_start_entry_by_id(db: Any, id: str) -> dict:
    """Mock function to look up correct race from list."""
    return next(start_entry for start_entry in START_ENTRIES if start_entry["id"] == id)


@pytest.mark.integration
async def test_create_startlist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_startlist: dict,
    startlist: dict,
) -> None:
    """Should return 405 Method Not Allowed."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=STARTLIST_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=STARTLIST_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_startlist, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/startlists", headers=headers, data=request_body)
        assert resp.status == 405


@pytest.mark.integration
async def test_get_startlist_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    startlist: dict,
) -> None:
    """Should return OK, and a body containing one startlist."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/startlists/{STARTLIST_ID}")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == STARTLIST_ID
        assert body["event_id"] == startlist["event_id"]
        assert len(body["start_entries"]) == len(startlist["start_entries"])
        for start_entry in body["start_entries"]:
            assert start_entry["race_id"]
            assert start_entry["bib"]
            assert start_entry["starting_position"]
            assert start_entry["scheduled_start_time"]


@pytest.mark.integration
async def test_get_startlist_by_event_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    startlist: dict,
) -> None:
    """Should return OK, and a body containing one startlist."""
    EVENT_ID = startlist["event_id"]
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=[startlist],
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        side_effect=get_start_entry_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/startlists?eventId={EVENT_ID}")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == STARTLIST_ID
        assert body[0]["event_id"] == startlist["event_id"]
        assert len(body[0]["start_entries"]) == len(startlist["start_entries"])
        for start_entry in body[0]["start_entries"]:
            assert start_entry["race_id"]
            assert start_entry["bib"]
            assert start_entry["starting_position"]
            assert start_entry["scheduled_start_time"]


@pytest.mark.integration
async def test_update_startlist_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
) -> None:
    """Should return 405 Method not allowed."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=STARTLIST_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(startlist, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/startlists/{STARTLIST_ID}", headers=headers, data=request_body
        )
        assert resp.status == 405


@pytest.mark.integration
async def test_get_all_startlists(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
) -> None:
    """Should return OK and a valid json body."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_all_startlists",
        return_value=[startlist],
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get("/startlists")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        startlists = await resp.json()
        assert type(startlists) is list
        assert len(startlists) > 0
        assert STARTLIST_ID == startlists[0]["id"]


@pytest.mark.integration
async def test_delete_startlist_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    start_entries: List[Dict],
    startlist: dict,
    races: List[Dict],
) -> None:
    """Should return No Content."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=STARTLIST_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
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
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(f"/startlists/{STARTLIST_ID}", headers=headers)
        assert resp.status == 204


# Bad cases


# Unauthorized cases:


@pytest.mark.integration
async def test_delete_startlist_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, startlist: dict
) -> None:
    """Should return 401 Unauthorized."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=STARTLIST_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.delete(f"/startlists/{STARTLIST_ID}")
        assert resp.status == 401


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_startlist_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    STARTLIST_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/startlists/{STARTLIST_ID}")
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_startlist_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    STARTLIST_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.delete_startlist",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.delete(f"/startlists/{STARTLIST_ID}", headers=headers)
        assert resp.status == 404
