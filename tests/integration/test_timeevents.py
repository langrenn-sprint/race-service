"""Integration test cases for the timeevents route."""
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
async def new_timeevent() -> dict:
    """Create a timeevent object."""
    return {
        "bib": 14,
        "event_id": "event_1",
        "race_id": "race_1",
        "point": "Finish",
        "rank": 0,
        "registration_time": "12:01:02",
        "next_race_id": "semi_1",
        "status": "OK",
        "changelog": "",
    }


@pytest.fixture
async def timeevent() -> dict:
    """Create a mock timeevent object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "bib": 14,
        "event_id": "event_1",
        "race_id": "race_1",
        "point": "Finish",
        "rank": 0,
        "registration_time": "12:01:02",
        "next_race_id": "semi_1",
        "status": "OK",
        "changelog": "hello",
    }


@pytest.fixture
async def timeevents() -> List:
    """Create a mock timeevent object."""
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
            "status": "OK",
            "changelog": "hello",
        }
    ]


@pytest.mark.integration
async def test_create_timeevent(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_timeevent: dict,
    timeevent: dict,
) -> None:
    """Should return Created, location header."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.services.timeevents_service.create_id",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.create_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_timeevent, indent=4, sort_keys=True, default=str)

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/timeevents", headers=headers, data=request_body)
        assert resp.status == 201
        assert f"/timeevents/{TIMEEVENT_ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_timeevent_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevent: dict
) -> None:
    """Should return OK, and a body containing one timeevent."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=timeevent,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/timeevents/{TIMEEVENT_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == TIMEEVENT_ID
        assert body["event_id"] == timeevent["event_id"]


@pytest.mark.integration
async def test_get_timeevents_by_event_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevents: List
) -> None:
    """Should return OK, and a body containing one timeevent."""
    EVENT_ID = timeevents[0]["event_id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=timeevents,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/timeevents?event-id={EVENT_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["event_id"] == timeevents[0]["event_id"]


@pytest.mark.integration
async def test_update_timeevent_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevent: dict
) -> None:
    """Should return No Content."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=timeevent,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.update_timeevent",
        return_value=TIMEEVENT_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = dumps(timeevent, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/timeevents/{TIMEEVENT_ID}", headers=headers, data=request_body
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_timeevents(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevent: dict
) -> None:
    """Should return OK and a valid json body."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_all_timeevents",
        return_value=[timeevent],
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get("/timeevents", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        timeevents = await resp.json()
        assert type(timeevents) is list
        assert len(timeevents) > 0
        assert TIMEEVENT_ID == timeevents[0]["id"]


@pytest.mark.integration
async def test_delete_timeevent_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevent: dict
) -> None:
    """Should return No Content."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=timeevent,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.delete_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(f"/timeevents/{TIMEEVENT_ID}", headers=headers)
        assert resp.status == 204


# Bad cases


@pytest.mark.integration
async def test_create_timeevent_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevent: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.services.timeevents_service.create_id",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.create_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    request_body = dumps(timeevent, indent=4, sort_keys=True, default=str)

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/timeevents", headers=headers, data=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_timeevent_adapter_fails(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_timeevent: dict
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "race_service.services.timeevents_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.create_timeevent",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_timeevent, indent=4, sort_keys=True, default=str)

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/timeevents", headers=headers, data=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_timeevent_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevent: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=timeevent,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.update_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": TIMEEVENT_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.post("/timeevents", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_update_timeevent_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevent: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=timeevent,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.update_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": TIMEEVENT_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/timeevents/{TIMEEVENT_ID}", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_timeevent_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevent: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=timeevent,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.update_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    update_body = deepcopy(timeevent)
    update_body["id"] = "different_id"
    request_body = dumps(update_body, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/timeevents/{TIMEEVENT_ID}", headers=headers, data=request_body
        )
        assert resp.status == 422


# Unauthorized cases:


@pytest.mark.integration
async def test_create_timeevent_no_authorization(
    client: _TestClient, mocker: MockFixture, new_timeevent: dict
) -> None:
    """Should return 401 Unauthorized."""
    TIMEEVENT_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.timeevents_service.create_id",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.create_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_timeevent, indent=4, sort_keys=True, default=str)
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.post("/timeevents", headers=headers, data=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_get_timeevent_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, timeevent: dict
) -> None:
    """Should return 401 Unauthorized."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=timeevent,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.get(f"/timeevents/{TIMEEVENT_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_update_timeevent_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, timeevent: dict
) -> None:
    """Should return 401 Unauthorized."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=timeevent,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.update_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )

    request_body = dumps(timeevent, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.put(
            f"/timeevents/{TIMEEVENT_ID}", headers=headers, data=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_timeevents_no_authorization(
    client: _TestClient, mocker: MockFixture, timeevent: dict
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_all_timeevents",
        return_value=[timeevent],
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)
        resp = await client.get("/timeevents")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_timeevent_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, timeevent: dict
) -> None:
    """Should return 401 Unauthorized."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.delete_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.delete(f"/timeevents/{TIMEEVENT_ID}")
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_timeevent_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    new_timeevent: dict,
    timeevent: dict,
) -> None:
    """Should return 403 Forbidden."""
    TIMEEVENT_ID = timeevent["id"]
    mocker.patch(
        "race_service.services.timeevents_service.create_id",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.create_timeevent",
        return_value=TIMEEVENT_ID,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    request_body = dumps(new_timeevent, indent=4, sort_keys=True, default=str)
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=403)
        resp = await client.post("/timeevents", headers=headers, data=request_body)
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_timeevent_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    TIMEEVENT_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/timeevents/{TIMEEVENT_ID}", headers=headers)
        assert resp.status == 404


@pytest.mark.integration
async def test_update_timeevent_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, timeevent: dict
) -> None:
    """Should return 404 Not found."""
    TIMEEVENT_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.update_timeevent",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = dumps(timeevent, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/timeevents/{TIMEEVENT_ID}", headers=headers, data=request_body
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_timeevent_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    TIMEEVENT_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevent_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.delete_timeevent",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.timeevents_adapter.TimeeventsAdapter.get_timeevents_by_event_id",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.delete(f"/timeevents/{TIMEEVENT_ID}", headers=headers)
        assert resp.status == 404
