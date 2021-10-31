"""Integration test cases for the startlists route."""
from copy import deepcopy
from datetime import datetime
from json import dumps
import os

from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
import jwt
from multidict import MultiDict
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
        "no_of_contestants": 32,
        "start_entries": [
            {
                "race_id": "J15",
                "bib": 1,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:00:00"),
                "starting_position": 1,
                "id": None,
            },
            {
                "race_id": "J15",
                "bib": 2,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:00:30"),
                "starting_position": 2,
                "id": None,
            },
            {
                "race_id": "G15",
                "bib": 3,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:01:00"),
                "starting_position": 1,
                "id": None,
            },
            {
                "race_id": "G15",
                "bib": 4,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:01:30"),
                "starting_position": 2,
                "id": None,
            },
            {
                "race_id": "J16",
                "bib": 5,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:02:00"),
                "starting_position": 1,
                "id": None,
            },
            {
                "race_id": "J16",
                "bib": 6,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:02:30"),
                "starting_position": 2,
                "id": None,
            },
            {
                "race_id": "G16",
                "bib": 7,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:03:00"),
                "starting_position": 1,
                "id": None,
            },
            {
                "race_id": "G16",
                "bib": 8,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:03:30"),
                "starting_position": 2,
                "id": None,
            },
        ],
    }


@pytest.fixture
async def startlist() -> dict:
    """Create a mock startlist object."""
    return {
        "id": "1",
        "event_id": "event_1",
        "no_of_contestants": 32,
        "start_entries": [
            {
                "race_id": "J15",
                "bib": 1,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:00:00"),
                "starting_position": 1,
                "id": "11",
            },
            {
                "race_id": "J15",
                "bib": 2,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:00:30"),
                "starting_position": 2,
                "id": "22",
            },
            {
                "race_id": "G15",
                "bib": 3,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:01:00"),
                "starting_position": 1,
                "id": "33",
            },
            {
                "race_id": "G15",
                "bib": 4,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:01:30"),
                "starting_position": 2,
                "id": "44",
            },
            {
                "race_id": "J16",
                "bib": 5,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:02:00"),
                "starting_position": 1,
                "id": "55",
            },
            {
                "race_id": "J16",
                "bib": 6,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:02:30"),
                "starting_position": 2,
                "id": "66",
            },
            {
                "race_id": "G16",
                "bib": 7,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:03:00"),
                "starting_position": 1,
                "id": "77",
            },
            {
                "race_id": "G16",
                "bib": 8,
                "scheduled_start_time": datetime.fromisoformat("2021-08-31 12:03:30"),
                "starting_position": 2,
                "id": "88",
            },
        ],
    }


@pytest.mark.integration
async def test_create_startlist(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_startlist: dict,
    startlist: dict,
) -> None:
    """Should return Created, location header."""
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

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/startlists", headers=headers, data=request_body)
        assert resp.status == 201
        assert f"/startlists/{STARTLIST_ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_startlist_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
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

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/startlists/{STARTLIST_ID}", headers=headers)
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
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
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

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/startlists?eventId={EVENT_ID}", headers=headers)
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
    """Should return No Content."""
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

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = dumps(startlist, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/startlists/{STARTLIST_ID}", headers=headers, data=request_body
        )
        assert resp.status == 204


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

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get("/startlists", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        startlists = await resp.json()
        assert type(startlists) is list
        assert len(startlists) > 0
        assert STARTLIST_ID == startlists[0]["id"]


@pytest.mark.integration
async def test_delete_startlist_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
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

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(f"/startlists/{STARTLIST_ID}", headers=headers)
        assert resp.status == 204


# Bad cases


@pytest.mark.integration
async def test_create_startlist_when_event_already_has_one(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_startlist: dict,
    startlist: dict,
) -> None:
    """Should return 400 Bad request."""
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
        return_value=[{"id": "blabladibla"}],
    )

    request_body = dumps(new_startlist, indent=4, sort_keys=True, default=str)

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/startlists", headers=headers, data=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_startlist_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
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

    request_body = dumps(startlist, indent=4, sort_keys=True, default=str)

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/startlists", headers=headers, data=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_startlist_adapter_fails(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_startlist: dict
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "race_service.services.startlists_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.create_startlist",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_startlist, indent=4, sort_keys=True, default=str)

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/startlists", headers=headers, data=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_startlist_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=STARTLIST_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": STARTLIST_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.post("/startlists", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_update_startlist_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=STARTLIST_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": STARTLIST_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/startlists/{STARTLIST_ID}", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_startlist_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=STARTLIST_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    update_body = deepcopy(startlist)
    update_body["id"] = "different_id"
    request_body = dumps(update_body, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/startlists/{STARTLIST_ID}", headers=headers, data=request_body
        )
        assert resp.status == 422


# Unauthorized cases:


@pytest.mark.integration
async def test_create_startlist_no_authorization(
    client: _TestClient, mocker: MockFixture, new_startlist: dict
) -> None:
    """Should return 401 Unauthorized."""
    STARTLIST_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
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
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.post("/startlists", headers=headers, data=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_get_startlist_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, startlist: dict
) -> None:
    """Should return 401 Unauthorized."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.get(f"/startlists/{STARTLIST_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_update_startlist_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, startlist: dict
) -> None:
    """Should return 401 Unauthorized."""
    STARTLIST_ID = startlist["id"]
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=STARTLIST_ID,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )

    request_body = dumps(startlist, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.put(
            f"/startlists/{STARTLIST_ID}", headers=headers, data=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_startlists_no_authorization(
    client: _TestClient, mocker: MockFixture, startlist: dict
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_all_startlists",
        return_value=[startlist],
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)
        resp = await client.get("/startlists")
        assert resp.status == 401


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


# Forbidden:
@pytest.mark.integration
async def test_create_startlist_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    new_startlist: dict,
    startlist: dict,
) -> None:
    """Should return 403 Forbidden."""
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
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=403)
        resp = await client.post("/startlists", headers=headers, data=request_body)
        assert resp.status == 403


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

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/startlists/{STARTLIST_ID}", headers=headers)
        assert resp.status == 404


@pytest.mark.integration
async def test_update_startlist_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, startlist: dict
) -> None:
    """Should return 404 Not found."""
    STARTLIST_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = dumps(startlist, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/startlists/{STARTLIST_ID}", headers=headers, data=request_body
        )
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

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.delete(f"/startlists/{STARTLIST_ID}", headers=headers)
        assert resp.status == 404
