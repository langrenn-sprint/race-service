"""Integration test cases for the events route."""
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


@pytest.mark.integration
async def test_create_event(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return Created, location header."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    request_body = {
        "name": "Oslo Skagen sprint",
        "date": "2021-08-31",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 201
        assert f"/events/{ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return OK, and a body containing one event."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={
            "id": ID,
            "name": "Oslo Skagen sprint",
            "date": "2021-08-31",
            "organiser": "Lyn Ski",
            "webpage": "https://example.com",
            "information": "Testarr for å teste den nye løysinga.",
        },
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/events/{ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        event = await resp.json()
        assert type(event) is dict
        assert event["id"] == ID
        assert event["name"] == "Oslo Skagen sprint"
        assert event["date"] == "2021-08-31"
        assert event["organiser"] == "Lyn Ski"
        assert event["webpage"] == "https://example.com"
        assert event["information"] == "Testarr for å teste den nye løysinga."


@pytest.mark.integration
async def test_update_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": ID, "name": "Oslo Skagen sprint Oppdatert"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_events(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return OK and a valid json body."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_all_events",
        return_value=[{"id": ID, "name": "Oslo Skagen Sprint"}],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get("/events", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        events = await resp.json()
        assert type(events) is list
        assert len(events) > 0
        assert ID == events[0]["id"]


@pytest.mark.integration
async def test_delete_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return No Content."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=ID,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.delete(f"/events/{ID}", headers=headers)
        assert resp.status == 204


# Bad cases

# Mandatory properties missing at create and update:
@pytest.mark.integration
async def test_create_event_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    request_body = {"optional_property": "Optional_property"}
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_event_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    request_body = {"id": ID, "name": "Oslo Skagen sprint Oppdatert"}
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_event_adapter_fails(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=None,
    )
    request_body = {"name": "Oslo Skagen sprint Oppdatert"}
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_update_event_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": ID, "optional_property": "Optional_property"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_update_event_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": "different_id", "name": "Oslo Skagen sprint Oppdatert"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 422


# Unauthorized cases:


@pytest.mark.integration
async def test_create_event_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )

    request_body = {"name": "Oslo Skagen sprint"}
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_get_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.get(f"/events/{ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_update_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value={"id": ID, "name": "Oslo Skagen Sprint"},
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )
    request_body = {"id": ID, "name": "Oslo Skagen sprint Oppdatert"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_list_events_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_all_events",
        return_value=[{"id": ID, "name": "Oslo Skagen Sprint"}],
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get("/events")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture
) -> None:
    """Should return 401 Unauthorized."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.delete(f"/events/{ID}")
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_event_insufficient_role(
    client: _TestClient, mocker: MockFixture, token_unsufficient_role: MockFixture
) -> None:
    """Should return 403 Forbidden."""
    ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "event_service.services.events_service.create_id",
        return_value=ID,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.create_event",
        return_value=ID,
    )
    request_body = {"name": "Oslo Skagen sprint"}
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=403)
        resp = await client.post("/events", headers=headers, json=request_body)
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/events/{ID}", headers=headers)
        assert resp.status == 404


@pytest.mark.integration
async def test_update_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.update_event",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint Oppdatert",
    }

    ID = "does-not-exist"
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(f"/events/{ID}", headers=headers, json=request_body)
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    ID = "does-not-exist"
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "event_service.adapters.events_adapter.EventsAdapter.delete_event",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(f"/events/{ID}", headers=headers)
        assert resp.status == 404
