"""Integration test cases for the race_results route."""
from copy import deepcopy
from json import dumps
import os
from typing import Any, List

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


START_ENTRIES: List[dict] = [
    {
        "id": "start_entry_1",
        "race_id": "race_1",
        "startlist_id": "startlist_1",
        "bib": 1,
        "name": "Start nummber 1",
        "club": "the club",
        "scheduled_start_time": ("2021-08-31T12:00:00"),
        "starting_position": 1,
        "status": "",
        "changelog": [],
    },
    {
        "id": "start_entry_2",
        "race_id": "race_1",
        "startlist_id": "startlist_1",
        "bib": 2,
        "name": "Start nummber 2",
        "club": "the club",
        "scheduled_start_time": ("2021-08-31T12:00:30"),
        "starting_position": 2,
        "status": "",
        "changelog": [],
    },
]


TIME_EVENTS: List[dict] = [
    {
        "id": "time_event_1",
        "bib": 1,
        "event_id": "event_1",
        "name": "Petter Propell",
        "club": "Barnehagen",
        "race": "race_name",
        "race_id": "race_1",
        "timing_point": "Finish",
        "rank": 1,
        "registration_time": "12:01:02",
        "next_race": "semi_name1",
        "next_race_id": "semi_1",
        "next_race_position": 1,
        "status": "OK",
        "changelog": [
            {
                "timestamp": "2021-11-08T22:06:30",
                "user_id": "test",
                "comment": "hello",
            }
        ],
    },
    {
        "id": "time_event_2",
        "bib": 2,
        "event_id": "event_1",
        "name": "Petter Propell",
        "club": "Barnehagen",
        "race": "race_name",
        "race_id": "race_1",
        "timing_point": "Finish",
        "rank": 2,
        "registration_time": "12:02:02",
        "next_race": "semi_name1",
        "next_race_id": "semi_1",
        "next_race_position": 1,
        "status": "OK",
        "changelog": [
            {
                "timestamp": "2021-11-08T22:06:30",
                "user_id": "test",
                "comment": "hello",
            }
        ],
    },
]


@pytest.fixture
async def race_result() -> dict:
    """Create a mock race-result object."""
    return {
        "id": "race_result_1",
        "race_id": "race_1",
        "timing_point": "Finish",
        "no_of_contestants": 2,
        "ranking_sequence": ["time_event_1", "time_event_2"],
    }


@pytest.fixture
async def race() -> dict:
    """Create a mock race object."""
    return {
        "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
        "raceclass": "G16",
        "order": 1,
        "start_time": "2021-08-31T12:00:00",
        "no_of_contestants": 8,
        "event_id": "event_1",
        "raceplan_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "start_entries": ["11", "22", "33", "44", "55", "66", "77", "88"],
        "results": {"Finish": "race_result_1"},
        "round": "Q",
        "index": "",
        "heat": 1,
        "rule": {"A": {"S": {"A": 10, "C": 0}}},
        "datatype": "individual_sprint",
    }


def get_time_event_by_id(db: Any, id: str) -> dict:
    """Mock function to look up correct time-event from list."""
    return next(time_event for time_event in TIME_EVENTS if time_event["id"] == id)


@pytest.mark.integration
async def test_create_race_result(
    client: _TestClient,
    token: MockFixture,
) -> None:
    """Should return 405 Not allowed."""
    request_body = dumps({}, indent=4, sort_keys=True, default=str)

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.post(
            "races/1/race-results", headers=headers, data=request_body
        )
        assert resp.status == 405


@pytest.mark.integration
async def test_get_race_result_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    race_result: dict,
) -> None:
    """Should return OK, and a body containing one race_result."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}', headers=headers
        )
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == RACE_RESULT_ID
        assert body["race_id"] == race_result["race_id"]
        assert body["timing_point"] == race_result["timing_point"]
        assert body["no_of_contestants"] == race_result["no_of_contestants"]
        assert "ranking_sequence" in body
        assert type(body["ranking_sequence"]) is list
        for time_event in body["ranking_sequence"]:
            assert type(time_event) is dict
            expected_time_event = get_time_event_by_id(db=None, id=time_event["id"])
            assert time_event == expected_time_event


@pytest.mark.integration
async def test_update_race_result_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    race_result: dict,
) -> None:
    """Should return No Content."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=RACE_RESULT_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(race_result, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}',
            headers=headers,
            data=request_body,
        )
        assert resp.status == 204


@pytest.mark.integration
async def test_get_race_results_by_race_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    race_result: dict,
) -> None:
    """Should return OK and a valid json body."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get(f'races/{race["id"]}/race-results', headers=headers)
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        race_results = await resp.json()
        assert type(race_results) is list
        assert len(race_results) > 0
        assert RACE_RESULT_ID == race_results[0]["id"]
        for time_event in race_results[0]["ranking_sequence"]:
            assert type(time_event) is dict
            expected_time_event = get_time_event_by_id(db=None, id=time_event["id"])
            assert time_event == expected_time_event


@pytest.mark.integration
async def test_get_race_results_by_race_id_and_timing_point(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    race_result: dict,
) -> None:
    """Should return OK and a valid json body."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",  # noqa: B950
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.get(
            f'races/{race["id"]}/race-results?timingPoint={"Finish"}',
            headers=headers,
        )
        assert resp.status == 200
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        race_results = await resp.json()
        assert type(race_results) is list
        assert len(race_results) == 1
        assert "Finish" in race["results"]
        assert RACE_RESULT_ID == race_results[0]["id"]
        for time_event in race_results[0]["ranking_sequence"]:
            assert type(time_event) is dict
            expected_time_event = get_time_event_by_id(db=None, id=time_event["id"])
            assert time_event == expected_time_event


@pytest.mark.integration
async def test_delete_race_result(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    race_result: dict,
) -> None:
    """Should return No Content."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
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

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}', headers=headers
        )
        assert resp.status == 204


# Bad cases


@pytest.mark.integration
async def test_update_race_result_by_id_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    race_result: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=RACE_RESULT_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": RACE_RESULT_ID}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}',
            headers=headers,
            json=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_update_race_result_by_id_different_id_in_body(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    race_result: dict,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=RACE_RESULT_ID,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    update_body = deepcopy(race_result)
    update_body["id"] = "different_id"
    request_body = dumps(update_body, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.put(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}',
            headers=headers,
            data=request_body,
        )
        assert resp.status == 422


@pytest.mark.integration
async def test_delete_race_result_race_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    race_result: dict,
) -> None:
    """Should return No Content."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
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

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.delete(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}', headers=headers
        )
        assert resp.status == 500
        body = await resp.json()
        assert "DB is inconsistent: cannot find race" in body["detail"]


# Unauthorized cases:


@pytest.mark.integration
async def test_get_race_result_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race: dict, race_result: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.get(f'races/{race["id"]}/race-results/{RACE_RESULT_ID}')
        assert resp.status == 401


@pytest.mark.integration
async def test_update_race_result_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race: dict, race_result: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=RACE_RESULT_ID,
    )

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    request_body = dumps(race_result, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.put(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}',
            headers=headers,
            data=request_body,
        )
        assert resp.status == 401


@pytest.mark.integration
async def test_list_race_results_no_authorization(
    client: _TestClient, mocker: MockFixture, race: dict, race_result: dict
) -> None:
    """Should return 401 Unauthorized."""
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id",
        return_value=[race_result],
    )
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)
        resp = await client.get(f'races/{race["id"]}/race-results')
        assert resp.status == 401


@pytest.mark.integration
async def test_delete_race_result_by_id_no_authorization(
    client: _TestClient, mocker: MockFixture, race: dict, race_result: dict
) -> None:
    """Should return 401 Unauthorized."""
    RACE_RESULT_ID = race_result["id"]
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
        return_value=RACE_RESULT_ID,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=401)

        resp = await client.delete(f'races/{race["id"]}/race-results/{RACE_RESULT_ID}')
        assert resp.status == 401


# Forbidden:


# NOT FOUND CASES:


@pytest.mark.integration
async def test_get_race_result_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture, race: dict
) -> None:
    """Should return 404 Not found."""
    RACE_RESULT_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=None,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)

        resp = await client.get(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}', headers=headers
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_update_race_result_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
    race_result: dict,
) -> None:
    """Should return 404 Not found."""
    RACE_RESULT_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(race_result, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.put(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}',
            headers=headers,
            data=request_body,
        )
        assert resp.status == 404


@pytest.mark.integration
async def test_delete_race_result_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: dict,
) -> None:
    """Should return 404 Not found."""
    RACE_RESULT_ID = "does-not-exist"
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
        return_value=None,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post("http://users.example.com:8081/authorize", status=204)
        resp = await client.delete(
            f'races/{race["id"]}/race-results/{RACE_RESULT_ID}', headers=headers
        )
        assert resp.status == 404
