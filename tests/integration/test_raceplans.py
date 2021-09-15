"""Integration test cases for the raceplans route."""
from copy import deepcopy
from datetime import time
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
async def new_raceplan() -> dict:
    """Create a mock contestant object."""
    return {
        "event_id": "event_1",
        "races": [
            {
                "name": "G16K01",
                "raceclass": "G16",
                "order": 1,
                "start_time": time(12, 00, 00).isoformat(),
            },
            {
                "name": "G16K02",
                "raceclass": "G16",
                "order": 2,
                "start_time": time(12, 15, 00).isoformat(),
            },
            {
                "name": "G16K03",
                "raceclass": "G16",
                "order": 3,
                "start_time": time(12, 30, 00).isoformat(),
            },
            {
                "name": "G16K04",
                "raceclass": "G16",
                "order": 4,
                "start_time": time(12, 45, 00).isoformat(),
            },
        ],
    }


@pytest.fixture
async def raceplan() -> dict:
    """Create a mock contestant object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "event_id": "event_1",
        "races": [
            {
                "name": "G16K01",
                "raceclass": "G16",
                "order": 1,
                "start_time": time(12, 00, 00).isoformat(),
            },
            {
                "name": "G16K02",
                "raceclass": "G16",
                "order": 2,
                "start_time": time(12, 15, 00).isoformat(),
            },
            {
                "name": "G16K03",
                "raceclass": "G16",
                "order": 3,
                "start_time": time(12, 30, 00).isoformat(),
            },
            {
                "name": "G16K04",
                "raceclass": "G16",
                "order": 4,
                "start_time": time(12, 45, 00).isoformat(),
            },
        ],
    }


@pytest.mark.integration
async def test_create_raceplan(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_raceplan: dict,
    raceplan: dict,
) -> None:
    """Should return Created, location header."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=RACEPLAN_ID,
    )

    request_body = new_raceplan

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/raceplans", headers=headers, json=request_body)
        assert resp.status == 201
        assert f"/raceplans/{RACEPLAN_ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_raceplan_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceplan: dict
) -> None:
    """Should return OK, and a body containing one raceplan."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/raceplans/{RACEPLAN_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == RACEPLAN_ID
        assert body["event_id"] == raceplan["event_id"]
        assert len(body["races"]) == 4
        for race in body["races"]:
            assert race["name"]
            assert race["raceclass"]
            assert race["order"]
            assert race["start_time"]


@pytest.mark.integration
async def test_update_raceplan_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceplan: dict
) -> None:
    """Should return No Content."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=RACEPLAN_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = raceplan

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/raceplans/{RACEPLAN_ID}", headers=headers, json=request_body
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_raceplans(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceplan: dict
) -> None:
    """Should return OK and a valid json body."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_all_raceplans",
        return_value=[raceplan],
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.get("/raceplans", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        raceplans = await resp.json()
        assert type(raceplans) is list
        assert len(raceplans) > 0
        assert RACEPLAN_ID == raceplans[0]["id"]


@pytest.mark.integration
async def test_delete_raceplan_by_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceplan: dict
) -> None:
    """Should return No Content."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.delete_raceplan",
        return_value=RACEPLAN_ID,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.delete(f"/raceplans/{RACEPLAN_ID}", headers=headers)
        assert resp.status == 204


# Bad cases


@pytest.mark.integration
async def test_create_raceplan_with_input_id(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceplan: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=RACEPLAN_ID,
    )
    request_body = raceplan
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/raceplans", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_raceplan_adapter_fails(
    client: _TestClient, mocker: MockFixture, token: MockFixture, new_raceplan: dict
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=None,
    )
    request_body = new_raceplan
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post("/raceplans", headers=headers, json=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_raceplan_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceplan: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=RACEPLAN_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": RACEPLAN_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.post("/raceplans", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_update_raceplan_by_id_missing_mandatory_property(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceplan: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=RACEPLAN_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = {"id": RACEPLAN_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/raceplans/{RACEPLAN_ID}", headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_raceplan_by_id_different_id_in_body(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceplan: dict
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=RACEPLAN_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = deepcopy(raceplan)
    request_body["id"] = "different_id"

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.put(
            f"/raceplans/{RACEPLAN_ID}", headers=headers, json=request_body
        )
        assert resp.status == 422


# Unauthorized cases:


@pytest.mark.integration
async def test_create_raceplan_no_authorization(
    client: _TestClient, mocker: MockFixture, new_raceplan: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACEPLAN_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=RACEPLAN_ID,
    )

    request_body = new_raceplan
    headers = MultiDict({hdrs.CONTENT_TYPE: "application/json"})

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.post("/raceplans", headers=headers, json=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_get_raceplan_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, raceplan: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.get(f"/raceplans/{RACEPLAN_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_update_raceplan_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, raceplan: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=RACEPLAN_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
        },
    )
    request_body = raceplan

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.put(
            f"/raceplans/{RACEPLAN_ID}", headers=headers, json=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_raceplans_no_authorization(
    client: _TestClient, mocker: MockFixture, raceplan: dict
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_all_raceplans",
        return_value=[raceplan],
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.get("/raceplans")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_raceplan_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, raceplan: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.delete_raceplan",
        return_value=RACEPLAN_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)

        resp = await client.delete(f"/raceplans/{RACEPLAN_ID}")
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_raceplan_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    new_raceplan: dict,
    raceplan: dict,
) -> None:
    """Should return 403 Forbidden."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=RACEPLAN_ID,
    )
    request_body = new_raceplan
    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=403)
        resp = await client.post("/raceplans", headers=headers, json=request_body)
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_raceplan_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    RACEPLAN_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=None,
    )
    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)

        resp = await client.get(f"/raceplans/{RACEPLAN_ID}", headers=headers)
        assert resp.status == 404


@pytest.mark.integration
async def test_update_raceplan_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, raceplan: dict
) -> None:
    """Should return 404 Not found."""
    RACEPLAN_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    request_body = raceplan

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.put(
            f"/raceplans/{RACEPLAN_ID}", headers=headers, json=request_body
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_raceplan_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    RACEPLAN_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.delete_raceplan",
        return_value=None,
    )

    headers = MultiDict(
        {
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.delete(f"/raceplans/{RACEPLAN_ID}", headers=headers)
        assert resp.status == 404
