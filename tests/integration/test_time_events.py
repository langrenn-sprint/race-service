"""Integration test cases for the time_events route."""
from copy import deepcopy
from json import dumps
import os
from typing import List

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
async def new_time_event() -> dict:
    """Create a time_event object."""
    return {
        "bib": 14,
        "event_id": "event_1",
        "race_id": "race_1",
        "point": "Finish",
        "rank": "0",
        "registration_time": "12:01:02",
        "next_race_id": "semi_1",
        "next_race_position": 1,
        "status": "OK",
        "changelog": "",
    }


@pytest.fixture
async def time_event() -> dict:
    """Create a mock time_event object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "bib": 14,
        "event_id": "event_1",
        "race_id": "race_1",
        "point": "Finish",
        "rank": "0",
        "registration_time": "12:01:02",
        "next_race_id": "semi_1",
        "next_race_position": 1,
        "status": "OK",
        "changelog": "hello",
    }


@pytest.fixture
async def time_events() -> List:
    """Create a mock time_event object."""
    return [
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "bib": 14,
            "event_id": "event_1",
            "race_id": "race_1",
            "point": "Finish",
            "rank": 0,
            "registration_time": "12:01:02",
            "next_race_id": "semi_1",
            "next_race_position": 1,
            "status": "OK",
            "changelog": "hello",
        }
    ]


@pytest.mark.integration
async def test_create_time_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_time_event: dict,
    time_event: dict,
) -> None:
    """Should return OK, and a header containing time_event_id."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_time_event, indent=4, sort_keys=True, default=str)

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    # todo - fix header location
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == 201
        assert f"/time-events/{TIME_EVENT_ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_time_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: dict
) -> None:
    """Should return OK, and a body containing one time_event."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/time-events/{TIME_EVENT_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == TIME_EVENT_ID
        assert body["event_id"] == time_event["event_id"]


@pytest.mark.integration
async def test_get_time_events_by_event_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_events: List
) -> None:
    """Should return OK, and a body containing one time_event."""
    EVENT_ID = time_events[0]["event_id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=time_events,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/time-events?eventId={EVENT_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["event_id"] == time_events[0]["event_id"]


@pytest.mark.integration
async def test_get_time_events_by_event_id_and_point(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_events: List
) -> None:
    """Should return OK, and a body containing one time_event."""
    EVENT_ID = time_events[0]["event_id"]
    POINT = time_events[0]["point"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id_and_point",
        return_value=time_events,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(
            f"/time-events?eventId={EVENT_ID}&point={POINT}", headers=headers
        )
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["event_id"] == time_events[0]["event_id"]
        assert body[0]["point"] == time_events[0]["point"]


@pytest.mark.integration
async def test_get_time_events_by_race_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_events: List
) -> None:
    """Should return OK, and a body containing one time_event."""
    RACE_ID = time_events[0]["race_id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_race_id",
        return_value=time_events,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/time-events?raceId={RACE_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["race_id"] == time_events[0]["race_id"]


@pytest.mark.integration
async def test_update_time_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: dict
) -> None:
    """Should return No Content."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=TIME_EVENT_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = dumps(time_event, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/time-events/{TIME_EVENT_ID}", headers=headers, data=request_body
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_time_events(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: dict
) -> None:
    """Should return OK and a valid json body."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_all_time_events",
        return_value=[time_event],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get("/time-events", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        time_events = await resp.json()
        assert type(time_events) is list
        assert len(time_events) > 0
        assert TIME_EVENT_ID == time_events[0]["id"]


@pytest.mark.integration
async def test_delete_time_event_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: dict
) -> None:
    """Should return No Content."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(f"/time-events/{TIME_EVENT_ID}", headers=headers)
        assert resp.status == 204


# Bad cases


@pytest.mark.integration
async def test_create_time_event_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    request_body = dumps(time_event, indent=4, sort_keys=True, default=str)

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_time_event_adapter_fails(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_time_event: dict
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_time_event, indent=4, sort_keys=True, default=str)

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_time_event_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": TIME_EVENT_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.post("/time-events", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_update_time_event_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": TIME_EVENT_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/time-events/{TIME_EVENT_ID}", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_time_event_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    update_body = deepcopy(time_event)
    update_body["id"] = "different_id"
    request_body = dumps(update_body, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/time-events/{TIME_EVENT_ID}", headers=headers, data=request_body
        )
        assert resp.status == 422


# Unauthorized cases:


@pytest.mark.integration
async def test_create_time_event_no_authorization(
    client: _TestClient, mocker: MockFixture, new_time_event: dict
) -> None:
    """Should return 401 Unauthorized."""
    TIME_EVENT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_time_event, indent=4, sort_keys=True, default=str)
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_get_time_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, time_event: dict
) -> None:
    """Should return 401 Unauthorized."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.get(f"/time-events/{TIME_EVENT_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_update_time_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, time_event: dict
) -> None:
    """Should return 401 Unauthorized."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=time_event,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )

    request_body = dumps(time_event, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.put(
            f"/time-events/{TIME_EVENT_ID}", headers=headers, data=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_time_events_no_authorization(
    client: _TestClient, mocker: MockFixture, time_event: dict
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_all_time_events",
        return_value=[time_event],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)
        resp = await client.get("/time-events")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_time_event_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, time_event: dict
) -> None:
    """Should return 401 Unauthorized."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.delete(f"/time-events/{TIME_EVENT_ID}")
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_time_event_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    new_time_event: dict,
    time_event: dict,
) -> None:
    """Should return 403 Forbidden."""
    TIME_EVENT_ID = time_event["id"]
    mocker.patch(
        "race_service.services.time_events_service.create_id",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.create_time_event",
        return_value=TIME_EVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_time_event, indent=4, sort_keys=True, default=str)
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=403)
        resp = await client.post("/time-events", headers=headers, data=request_body)
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_time_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    TIME_EVENT_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/time-events/{TIME_EVENT_ID}", headers=headers)
        assert resp.status == 404


@pytest.mark.integration
async def test_update_time_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, time_event: dict
) -> None:
    """Should return 404 Not found."""
    TIME_EVENT_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.update_time_event",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = dumps(time_event, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/time-events/{TIME_EVENT_ID}", headers=headers, data=request_body
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_time_event_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    TIME_EVENT_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.delete_time_event",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_events_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.delete(f"/time-events/{TIME_EVENT_ID}", headers=headers)
        assert resp.status == 404
