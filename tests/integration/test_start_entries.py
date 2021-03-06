"""Integration test cases for the start_entries route."""
from copy import deepcopy
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
async def race() -> dict:
    """Create a mock race object."""
    return {
        "id": "race_1",
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 8,
        "max_no_of_contestants": 10,
        "event_id": "event_1",
        "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "start_entries": [],
        "results": {},
        "round": "Q",
        "index": "",
        "heat": 1,
        "rule": {"A": {"S": {"A": 10, "C": 0}}},
        "datatype": "individual_sprint",
    }


@pytest.fixture
async def startlist() -> dict:
    """Create a startlist object."""
    return {
        "id": "startlist_1",
        "event_id": "event_1",
        "no_of_contestants": 0,
        "start_entries": [],
    }


@pytest.fixture
async def new_start_entry() -> dict:
    """Create a start_entry object."""
    return {
        "race_id": "race_1",
        "startlist_id": "startlist_1",
        "bib": 1,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": ("2021-08-31T12:00:00"),
        "starting_position": 1,
    }


@pytest.fixture
async def start_entry() -> dict:
    """Create a mock start_entry object."""
    return {
        "id": "start_entry_1",
        "race_id": "race_1",
        "startlist_id": "startlist_1",
        "bib": 1,
        "name": "name names",
        "club": "the club",
        "scheduled_start_time": ("2021-08-31T12:00:00"),
        "starting_position": 1,
        "status": "",
        "changelog": [],
    }


@pytest.mark.integration
async def test_create_start_entry(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    startlist: dict,
    new_start_entry: dict,
    start_entry: dict,
) -> None:
    """Should return Created, location header."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_bib",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(new_start_entry, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post(
            "races/1/start-entries", headers=headers, data=request_body
        )
        assert resp.status == 201
        assert (
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}'
            in resp.headers[hdrs.LOCATION]
        )


@pytest.mark.integration
async def test_get_start_entry_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
) -> None:
    """Should return OK, and a body containing one start_entry."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f'races/{race["id"]}/start-entries/{START_ENTRY_ID}')
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == START_ENTRY_ID
        assert body["startlist_id"] == start_entry["startlist_id"]
        assert body["race_id"] == start_entry["race_id"]
        assert body["bib"] == start_entry["bib"]
        assert body["starting_position"] == start_entry["starting_position"]
        assert body["scheduled_start_time"] == start_entry["scheduled_start_time"]
        assert body["name"] == start_entry["name"]
        assert body["club"] == start_entry["club"]
        assert body["status"] == start_entry["status"]
        assert body["changelog"] == start_entry["changelog"]


@pytest.mark.integration
async def test_update_start_entry_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
) -> None:
    """Should return No Content."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=START_ENTRY_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(start_entry, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}',
            headers=headers,
            data=request_body,
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_get_start_entries_by_bib(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
) -> None:
    """Should return OK and a valid json body."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_bib",
        return_value=[start_entry],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get(f"races/all/start-entries?bib={start_entry['bib']}")
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        start_entries = await resp.json()
        assert type(start_entries) is list
        assert len(start_entries) > 0
        assert START_ENTRY_ID == start_entries[0]["id"]


@pytest.mark.integration
async def test_get_start_entries_by_race_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
) -> None:
    """Should return OK and a valid json body."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get(f'races/{race["id"]}/start-entries')
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        start_entries = await resp.json()
        assert type(start_entries) is list
        assert len(start_entries) > 0
        assert START_ENTRY_ID == start_entries[0]["id"]


@pytest.mark.integration
async def test_get_start_entries_by_race_id_and_startlist_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    startlist: dict,
    start_entry: dict,
) -> None:
    """Should return OK and a valid json body."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id_and_startlist_id",  # noqa: B950
        return_value=[start_entry],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get(
            f'races/{race["id"]}/start-entries?startlistId={startlist["id"]}'
        )
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        start_entries = await resp.json()
        assert type(start_entries) is list
        assert len(start_entries) > 0
        assert START_ENTRY_ID == start_entries[0]["id"]


@pytest.mark.integration
async def test_delete_start_entry(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    startlist: dict,
    start_entry: dict,
) -> None:
    """Should return No Content."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}', headers=headers
        )
        assert resp.status == 204


# Bad cases


@pytest.mark.integration
async def test_create_start_entry_race_is_full(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    startlist: dict,
    new_start_entry: dict,
    start_entry: dict,
) -> None:
    """Should return 400 Bad request."""
    START_ENTRY_ID = start_entry["id"]
    full_race = deepcopy(race)
    full_race["start_entries"] = [
        s % s for s in range(1, race["max_no_of_contestants"] + 1)
    ]
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=full_race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(new_start_entry, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post(
            "races/1/start-entries", headers=headers, data=request_body
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_create_start_entry_race_bib_already_in_race(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    startlist: dict,
    new_start_entry: dict,
    start_entry: dict,
) -> None:
    """Should return 400 Bad request."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(new_start_entry, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post(
            "races/1/start-entries", headers=headers, data=request_body
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_create_start_entry_race_position_is_taken(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    startlist: dict,
    new_start_entry: dict,
    start_entry: dict,
) -> None:
    """Should return 400 Bad request."""
    START_ENTRY_ID = start_entry["id"]
    start_entry_different_bib_same_starting_position = deepcopy(start_entry)
    start_entry_different_bib_same_starting_position["bib"] = 1000
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=[start_entry_different_bib_same_starting_position],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(new_start_entry, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post(
            "races/1/start-entries", headers=headers, data=request_body
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_create_start_entry_with_input_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
    startlist: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(start_entry, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post(
            f'races/{race["id"]}/start-entries', headers=headers, data=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_create_start_entry_adapter_fails(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
    startlist: dict,
    new_start_entry: dict,
) -> None:
    """Should return 400 HTTPBadRequest."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    request_body = dumps(new_start_entry, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post(
            f'races/{race["id"]}/start-entries', headers=headers, data=request_body
        )
        assert resp.status == 400


@pytest.mark.integration
async def test_create_start_entry_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entries_by_race_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": START_ENTRY_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.post(
            f'races/{race["id"]}/start-entries', headers=headers, json=request_body
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_start_entry_by_id_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=START_ENTRY_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": START_ENTRY_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}',
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_start_entry_by_id_different_id_in_body(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=START_ENTRY_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    update_body = deepcopy(start_entry)
    update_body["id"] = "different_id"
    request_body = dumps(update_body, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}',
            headers=headers,
            data=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_delete_start_entry_race_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    startlist: dict,
    start_entry: dict,
) -> None:
    """Should return 404 Not found."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=startlist,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}', headers=headers
        )
        assert resp.status == 404
        body = await resp.json()
        assert "DB is inconsistent: cannot find race with id" in body["detail"]


@pytest.mark.integration
async def test_delete_start_entry_startlist_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    startlist: dict,
    start_entry: dict,
) -> None:
    """Should return 404 Not found."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.get_startlist_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.startlists_adapter.StartlistsAdapter.update_startlist",
        return_value=True,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}', headers=headers
        )
        assert resp.status == 404
        body = await resp.json()
        assert "DB is inconsistent: cannot find startlist with id" in body["detail"]


# Unauthorized cases:


@pytest.mark.integration
async def test_create_start_entry_no_authorization(
    client: _TestClient, mocker: MockFixture, race: dict, new_start_entry: dict
) -> None:
    """Should return 401 Unauthorized."""
    START_ENTRY_ID = "290e70d5-0933-4af0-bb53-1d705ba7eb95"
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=START_ENTRY_ID,
    )

    request_body = dumps(new_start_entry, indent=4, sort_keys=True, default=str)

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.post(
            f'races/{race["id"]}/start-entries', headers=headers, data=request_body
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_update_start_entry_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race: dict, start_entry: dict
) -> None:
    """Should return 401 Unauthorized."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=start_entry,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=START_ENTRY_ID,
    )

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    request_body = dumps(start_entry, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.put(
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}',
            headers=headers,
            data=request_body,
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_start_entry_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race: dict, start_entry: dict
) -> None:
    """Should return 401 Unauthorized."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=START_ENTRY_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.delete(f'races/{race["id"]}/start-entries/{START_ENTRY_ID}')
        assert resp.status == 401


# Forbidden:
@pytest.mark.integration
async def test_create_start_entry_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token_unsufficient_role: MockFixture,
    race: dict,
    new_start_entry: dict,
    start_entry: dict,
) -> None:
    """Should return 403 Forbidden."""
    START_ENTRY_ID = start_entry["id"]
    mocker.patch(
        "race_service.services.start_entries_service.create_id",
        return_value=START_ENTRY_ID,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.create_start_entry",
        return_value=START_ENTRY_ID,
    )

    request_body = dumps(new_start_entry, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token_unsufficient_role}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=403)
        resp = await client.post(
            f'races/{race["id"]}/start-entries', headers=headers, data=request_body
        )
        assert resp.status == 403


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_start_entry_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, race: dict
) -> None:
    """Should return 404 Not found."""
    START_ENTRY_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=None,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(f'races/{race["id"]}/start-entries/{START_ENTRY_ID}')
        assert resp.status == 404


@pytest.mark.integration
async def test_update_start_entry_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    start_entry: dict,
) -> None:
    """Should return 404 Not found."""
    START_ENTRY_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.update_start_entry",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(start_entry, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.put(
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}',
            headers=headers,
            data=request_body,
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_start_entry_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
) -> None:
    """Should return 404 Not found."""
    START_ENTRY_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.get_start_entry_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.start_entries_adapter.StartEntriesAdapter.delete_start_entry",
        return_value=None,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.delete(
            f'races/{race["id"]}/start-entries/{START_ENTRY_ID}', headers=headers
        )
        assert resp.status == 404
