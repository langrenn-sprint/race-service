"""Integration test cases for the races route."""
from copy import deepcopy
from datetime import datetime
from json import dumps
import os

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
async def new_race_interval_start() -> dict:
    """Create a race object."""
    return {
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 8,
        "event_id": "event_1",
        "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "start_entries": [],
        "datatype": "interval_start",
    }


@pytest.fixture
async def race_interval_start() -> dict:
    """Create a mock race object."""
    return {
        "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 8,
        "event_id": "event_1",
        "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "start_entries": [],
        "datatype": "interval_start",
    }


@pytest.fixture
async def new_race_individual_sprint() -> dict:
    """Create a mock race object."""
    return {
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 8,
        "event_id": "event_1",
        "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "start_entries": [],
        "round": "Q",
        "index": "",
        "heat": 1,
        "rule": {"A": {"S": {"A": 10, "C": 0}}},
        "datatype": "individual_sprint",
    }


@pytest.fixture
async def race_individual_sprint() -> dict:
    """Create a mock race object."""
    return {
        "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 8,
        "event_id": "event_1",
        "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "start_entries": [],
        "round": "Q",
        "index": "",
        "heat": 1,
        "rule": {"A": {"S": {"A": 10, "C": 0}}},
        "datatype": "individual_sprint",
    }


@pytest.fixture
async def new_race_unsupported_datatype() -> dict:
    """Create a race object."""
    return {
        "raceclass": "G16",
        "order": 1,
        "start_time": datetime.fromisoformat("2021-08-31 12:00:00"),
        "no_of_contestants": 8,
        "datatype": "unsupported",
    }


@pytest.mark.integration
async def test_create_race_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_race_interval_start: dict,
    race_interval_start: dict,
) -> None:
    """Should return Created, location header."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.services.races_service.create_id",
        return_value=RACE_ID,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=RACE_ID,
    )

    request_body = dumps(new_race_interval_start, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/races", headers=headers, data=request_body)
        assert resp.status == 201
        assert f"/races/{RACE_ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_create_race_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_race_individual_sprint: dict,
    race_individual_sprint: dict,
) -> None:
    """Should return Created, location header."""
    RACE_ID = race_individual_sprint["id"]
    mocker.patch(
        "race_service.services.races_service.create_id",
        return_value=RACE_ID,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=RACE_ID,
    )

    request_body = dumps(
        new_race_individual_sprint, indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/races", headers=headers, data=request_body)
        assert resp.status == 201
        assert f"/races/{RACE_ID}" in resp.headers[hdrs.LOCATION]


@pytest.mark.integration
async def test_get_race_by_id_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return OK, and a body containing one race."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/races/{RACE_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == RACE_ID
        assert body["event_id"] == race_interval_start["event_id"]
        assert body["raceclass"] == race_interval_start["raceclass"]
        assert body["order"] == race_interval_start["order"]
        assert body["start_time"] == race_interval_start["start_time"]
        assert body["no_of_contestants"] == race_interval_start["no_of_contestants"]
        assert body["event_id"] == race_interval_start["event_id"]
        assert body["start_entries"] == race_interval_start["start_entries"]
        assert body["datatype"] == race_interval_start["datatype"]


@pytest.mark.integration
async def test_get_race_by_id_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_individual_sprint: dict,
) -> None:
    """Should return OK, and a body containing one race."""
    RACE_ID = race_individual_sprint["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_individual_sprint,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/races/{RACE_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == RACE_ID
        assert body["event_id"] == race_individual_sprint["event_id"]
        assert body["raceclass"] == race_individual_sprint["raceclass"]
        assert body["order"] == race_individual_sprint["order"]
        assert body["start_time"] == race_individual_sprint["start_time"]
        assert body["no_of_contestants"] == race_individual_sprint["no_of_contestants"]
        assert body["event_id"] == race_individual_sprint["event_id"]
        assert body["start_entries"] == race_individual_sprint["start_entries"]
        assert body["round"] == race_individual_sprint["round"]
        assert body["index"] == race_individual_sprint["index"]
        assert body["heat"] == race_individual_sprint["heat"]
        assert body["rule"] == race_individual_sprint["rule"]
        assert body["datatype"] == race_individual_sprint["datatype"]


@pytest.mark.integration
async def test_get_races_by_event_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return OK, and a body containing one race."""
    EVENT_ID = race_interval_start["event_id"]
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=[race_interval_start],
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/races?eventId={EVENT_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == RACE_ID
        assert body[0]["event_id"] == race_interval_start["event_id"]
        assert body[0]["raceclass"] == race_interval_start["raceclass"]
        assert body[0]["order"] == race_interval_start["order"]
        assert body[0]["start_time"] == race_interval_start["start_time"]
        assert body[0]["no_of_contestants"] == race_interval_start["no_of_contestants"]
        assert body[0]["event_id"] == race_interval_start["event_id"]
        assert body[0]["start_entries"] == race_interval_start["start_entries"]
        assert body[0]["datatype"] == race_interval_start["datatype"]


@pytest.mark.integration
async def test_get_races_by_event_id_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_individual_sprint: dict,
) -> None:
    """Should return OK, and a body containing one race."""
    EVENT_ID = race_individual_sprint["event_id"]
    RACE_ID = race_individual_sprint["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_races_by_event_id",
        return_value=[race_individual_sprint],
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/races?eventId={EVENT_ID}", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == RACE_ID
        assert body[0]["raceclass"] == race_individual_sprint["raceclass"]
        assert body[0]["order"] == race_individual_sprint["order"]
        assert body[0]["start_time"] == race_individual_sprint["start_time"]
        assert (
            body[0]["no_of_contestants"] == race_individual_sprint["no_of_contestants"]
        )
        assert body[0]["event_id"] == race_individual_sprint["event_id"]
        assert body[0]["start_entries"] == race_individual_sprint["start_entries"]
        assert body[0]["round"] == race_individual_sprint["round"]
        assert body[0]["index"] == race_individual_sprint["index"]
        assert body[0]["heat"] == race_individual_sprint["heat"]
        assert body[0]["rule"] == race_individual_sprint["rule"]
        assert body[0]["datatype"] == race_individual_sprint["datatype"]


@pytest.mark.integration
async def test_update_race_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return No Content."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=RACE_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(race_interval_start, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(f"/races/{RACE_ID}", headers=headers, data=request_body)
        assert resp.status == 204


@pytest.mark.integration
async def test_get_all_races(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return OK and a valid json body."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_all_races",
        return_value=[race_interval_start],
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get("/races", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        races = await resp.json()
        assert type(races) is list
        assert len(races) > 0
        assert RACE_ID == races[0]["id"]


@pytest.mark.integration
async def test_get_all_races_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_individual_sprint: dict,
) -> None:
    """Should return OK and a valid json body."""
    RACE_ID = race_individual_sprint["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_all_races",
        return_value=[race_individual_sprint],
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get("/races", headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) > 0
        assert RACE_ID == body[0]["id"]


@pytest.mark.integration
async def test_delete_race_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return No Content."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=RACE_ID,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(f"/races/{RACE_ID}", headers=headers)
        assert resp.status == 204


# Bad cases


@pytest.mark.integration
async def test_create_race_unsupported_datatype(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_race_unsupported_datatype: dict,
    race_interval_start: dict,
) -> None:
    """Should return Created, location header."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.services.races_service.create_id",
        return_value=RACE_ID,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=RACE_ID,
    )

    request_body = dumps(
        new_race_unsupported_datatype, indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/races", headers=headers, data=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_race_with_input_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.services.races_service.create_id",
        return_value=RACE_ID,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=RACE_ID,
    )

    request_body = dumps(race_interval_start, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/races", headers=headers, data=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_create_race_adapter_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_race_interval_start: dict,
) -> None:
    """Should return 400 HTTPBadRequest."""
    mocker.patch(
        "race_service.services.races_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=None,
    )

    request_body = dumps(new_race_interval_start, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post("/races", headers=headers, data=request_body)
        assert resp.status == 400


@pytest.mark.integration
async def test_create_race_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.services.races_service.create_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": RACE_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.post("/races", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_update_race_by_id_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=RACE_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": RACE_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(f"/races/{RACE_ID}", headers=headers, json=request_body)
        assert resp.status == 422


@pytest.mark.integration
async def test_update_race_by_id_different_id_in_body(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=RACE_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    update_body = deepcopy(race_interval_start)
    update_body["id"] = "different_id"
    request_body = dumps(update_body, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(f"/races/{RACE_ID}", headers=headers, data=request_body)
        assert resp.status == 422


# Unauthorized cases:


@pytest.mark.integration
async def test_create_race_no_authorization(
    client: _TestClient, mocker: MockFixture, new_race_interval_start: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACE_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.races_service.create_id",
        return_value=RACE_ID,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=RACE_ID,
    )

    request_body = dumps(new_race_interval_start, indent=4, sort_keys=True, default=str)

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.post("/races", headers=headers, data=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_get_race_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race_interval_start: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.get(f"/races/{RACE_ID}")
        assert resp.status == 401


@pytest.mark.integration
async def test_update_race_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race_interval_start: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=RACE_ID,
    )

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    request_body = dumps(race_interval_start, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.put(f"/races/{RACE_ID}", headers=headers, data=request_body)
        assert resp.status == 401


@pytest.mark.integration
async def test_list_races_no_authorization(
    client: _TestClient, mocker: MockFixture, race_interval_start: dict
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_all_races",
        return_value=[race_interval_start],
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)
        resp = await client.get("/races")
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_race_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race_interval_start: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=RACE_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.delete(f"/races/{RACE_ID}")
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_race_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    new_race_interval_start: dict,
    race_interval_start: dict,
) -> None:
    """Should return 403 Forbidden."""
    RACE_ID = race_interval_start["id"]
    mocker.patch(
        "race_service.services.races_service.create_id",
        return_value=RACE_ID,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        return_value=RACE_ID,
    )

    request_body = dumps(new_race_interval_start, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=403)
        resp = await client.post("/races", headers=headers, data=request_body)
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_race_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    RACE_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=None,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f"/races/{RACE_ID}", headers=headers)
        assert resp.status == 404


@pytest.mark.integration
async def test_update_race_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race_interval_start: dict,
) -> None:
    """Should return 404 Not found."""
    RACE_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(race_interval_start, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.put(f"/races/{RACE_ID}", headers=headers, data=request_body)
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_race_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    RACE_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=None,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.delete(f"/races/{RACE_ID}", headers=headers)
        assert resp.status == 404
