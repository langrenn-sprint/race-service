"""Integration test cases for the raceplans route."""
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
async def request_body() -> dict:
    """Create a mock request_body object."""
    return {
        "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "competition_format": "Individual sprint competition",
        "raceclasses": [{"name": "G16", "order": "1"}, {"name": "J16", "order": "2"}],
        "contestants": [
            {"bib": 1, "raceclass": "G16"},
            {"bib": 2, "raceclass": "G16"},
            {"bib": 3, "raceclass": "J16"},
            {"bib": 4, "raceclass": "J16"},
        ],
    }


@pytest.fixture
async def raceplan() -> dict:
    """Create a mock raceplan object."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "G 16 år",
        "order": 1,
        "raceclass": "G16",
        "event_id": "ref_to_event",
        "distance": "5km",
    }


@pytest.mark.integration
async def test_generate_raceplan_for_event(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    request_body: dict,
    raceplan: dict,
) -> None:
    """Should return 201 Created, location header."""
    RACEPLAN_ID = raceplan["id"]
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=RACEPLAN_ID,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=RACEPLAN_ID,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    body = request_body
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=204)
        resp = await client.post(
            "/raceplans/generate-raceplan-for-event", headers=headers, json=body
        )
        assert resp.status == 201
        assert f"/raceplans/{RACEPLAN_ID}" in resp.headers[hdrs.LOCATION]


# Not authenticated
@pytest.mark.integration
async def test_generate_raceplan_for_event_unauthorized(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    request_body: dict,
    raceplan: dict,
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan,
    )

    headers = MultiDict(
        {
            hdrs.CONTENT_TYPE: "application/json",
            hdrs.AUTHORIZATION: f"Bearer {token}",
        },
    )
    body = request_body
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://example.com:8081/authorize", status=401)
        resp = await client.post(
            "/raceplans/generate-raceplan-for-event", headers=headers, json=body
        )
        assert resp.status == 401
