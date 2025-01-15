"""Integration test cases for the race_results route."""

import os
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from json import dumps
from typing import Any

import jwt
import pytest
from aiohttp import hdrs
from aiohttp.test_utils import TestClient as _TestClient
from aioresponses import aioresponses
from pytest_mock import MockFixture

from race_service.adapters import RaceNotFoundError, RaceResultNotFoundError
from race_service.models import Changelog, IndividualSprintRace, RaceResult, TimeEvent

USERS_HOST_SERVER = os.getenv("USERS_HOST_SERVER")
USERS_HOST_PORT = os.getenv("USERS_HOST_PORT")


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": os.getenv("ADMIN_USERNAME"), "roles": ["admin"]}
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"identity": "user", "roles": ["user"]}
    return jwt.encode(payload, secret, algorithm)


TIME_EVENTS: list[TimeEvent] = [
    TimeEvent(
        id="time_event_1",
        bib=1,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="race_1",
        timing_point="Finish",
        rank=1,
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        next_race="semi_name1",
        next_race_id="semi_1",
        next_race_position=1,
        status="OK",
        changelog=[
            Changelog(
                timestamp=datetime.fromisoformat("2021-11-08T22:06:30"),
                user_id="test",
                comment="hello",
            )
        ],
    ),
    TimeEvent(
        id="time_event_2",
        bib=2,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="race_1",
        timing_point="Finish",
        rank=2,
        registration_time=datetime.fromisoformat("2023-02-11T12:02:02"),
        next_race="semi_name1",
        next_race_id="semi_1",
        next_race_position=1,
        status="OK",
        changelog=[
            Changelog(
                timestamp=datetime.fromisoformat("2021-11-08T22:06:30"),
                user_id="test",
                comment="hello",
            )
        ],
    ),
    TimeEvent(
        id="time_event_3",
        bib=2,
        event_id="event_1",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="race_1",
        timing_point="Template",
        rank=2,
        registration_time=datetime.fromisoformat("2023-02-11T12:02:02"),
        next_race="semi_name1",
        next_race_id="semi_1",
        next_race_position=1,
        status="OK",
        changelog=[
            Changelog(
                timestamp=datetime.fromisoformat("2021-11-08T22:06:30"),
                user_id="test",
                comment="hello",
            )
        ],
    ),
]


@pytest.fixture
async def race_result() -> RaceResult:
    """Create a mock race-result object."""
    return RaceResult(
        id="race_result_1",
        race_id="race_1",
        timing_point="Finish",
        no_of_contestants=2,
        ranking_sequence=["time_event_1", "time_event_2"],
        status=0,
    )


@pytest.fixture
async def race() -> IndividualSprintRace:
    """Create a mock race object."""
    return IndividualSprintRace(
        id="190e70d5-0933-4af0-bb53-1d705ba7eb95",
        raceclass="G16",
        order=1,
        start_time=datetime.fromisoformat("2021-08-31T12:00:00"),
        no_of_contestants=8,
        max_no_of_contestants=10,
        event_id="event_1",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=["11", "22", "33", "44", "55", "66", "77", "88"],
        results={"Finish": "race_result_1"},
        round="Q",
        index="",
        heat=1,
        rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
        datatype="individual_sprint",
    )


def get_time_event_by_id(db: Any, id_: str) -> TimeEvent:
    """Mock function to look up correct time-event from list."""
    return next(time_event for time_event in TIME_EVENTS if time_event.id == id_)


@pytest.mark.integration
@pytest.mark.asyncio
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
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post(
            "races/1/race-results", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_result_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return OK, and a body containing one race_result."""
    race_result_id = race_result.id
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"races/{race.id}/race-results/{race_result_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == race_result_id
        assert body["race_id"] == race_result.race_id
        assert body["timing_point"] == race_result.timing_point
        assert body["no_of_contestants"] == race_result.no_of_contestants
        assert "ranking_sequence" in body
        assert type(body["ranking_sequence"]) is list
        assert (
            len(body["ranking_sequence"]) == len(TIME_EVENTS) - 1
        )  # Template should not be included
        for time_event in body["ranking_sequence"]:
            assert type(time_event) is dict
            expected_time_event = get_time_event_by_id(db=None, id_=time_event["id"])
            assert time_event == expected_time_event.to_dict()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return No Content."""
    race_result_id = race_result.id
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(race_result.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"races/{race.id}/race-results/{race_result_id}",
            headers=headers,
            data=request_body,
        )
        assert resp.status == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_results_by_race_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return OK and a valid json body."""
    race_result_id = race_result.id
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.get(f"races/{race.id}/race-results")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        race_results = await resp.json()
        assert type(race_results) is list
        assert len(race_results) > 0
        assert race_results[0]["id"] == race_result_id
        for time_event in race_results[0]["ranking_sequence"]:
            assert type(time_event) is dict
            expected_time_event = get_time_event_by_id(db=None, id_=time_event["id"])
            assert time_event == expected_time_event.to_dict()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_results_by_race_id_idsonly(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return OK and a valid json body."""
    race_result_id = race_result.id
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.get(f"races/{race.id}/race-results?idsOnly=true")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        race_results = await resp.json()
        assert type(race_results) is list
        assert len(race_results) > 0
        assert race_results[0]["id"] == race_result_id
        for time_event in race_results[0]["ranking_sequence"]:
            assert type(time_event) is str
            expected_time_event = get_time_event_by_id(db=None, id_=time_event)
            assert time_event == expected_time_event.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_results_by_race_id_and_timing_point(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return OK and a valid json body."""
    race_result_id = race_result.id
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "race_service.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.get(f"races/{race.id}/race-results?timingPoint={'Finish'}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        race_results = await resp.json()
        assert type(race_results) is list
        assert len(race_results) == 1
        assert "Finish" in race.results
        assert race_results[0]["id"] == race_result_id
        for time_event in race_results[0]["ranking_sequence"]:
            assert type(time_event) is dict
            expected_time_event = get_time_event_by_id(db=None, id_=time_event["id"])
            assert time_event == expected_time_event.to_dict()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return No Content."""
    race_result_id = race_result.id
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
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.delete(
            f"races/{race.id}/race-results/{race_result_id}", headers=headers
        )
        assert resp.status == HTTPStatus.NO_CONTENT


# Bad cases


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_by_id_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    race_result_id = race_result.id
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": race_result_id}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"races/{race.id}/race-results/{race_result_id}",
            headers=headers,
            json=request_body,
        )
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_by_id_different_id_in_body(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    race_result_id = race_result.id
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_id,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    update_body = deepcopy(race_result)
    update_body.id = "different_id"
    request_body = dumps(update_body.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"races/{race.id}/race-results/{race_result_id}",
            headers=headers,
            data=request_body,
        )
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result_race_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 404 Not found."""
    race_result_id = race_result.id
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
        side_effect=RaceNotFoundError(f"Race with id {race.id} not found."),
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.delete(
            f"races/{race.id}/race-results/{race_result_id}", headers=headers
        )
        assert resp.status == HTTPStatus.NOT_FOUND
        body = await resp.json()
        assert "DB is inconsistent: cannot find race" in body["detail"]


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_by_id_no_authorization(
    client: _TestClient,
    mocker: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 401 Unauthorized."""
    race_result_id = race_result.id
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_id,
    )

    headers = {hdrs.CONTENT_TYPE: "application/json"}

    request_body = dumps(race_result.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.put(
            f"races/{race.id}/race-results/{race_result_id}",
            headers=headers,
            data=request_body,
        )
        assert resp.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result_by_id_no_authorization(
    client: _TestClient,
    mocker: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 401 Unauthorized."""
    race_result_id = race_result.id
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundError(f"RaceResult with id {id} not found"),
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
        return_value=race_result_id,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.delete(f"races/{race.id}/race-results/{race_result_id}")
        assert resp.status == HTTPStatus.UNAUTHORIZED


# Forbidden:


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_result_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
) -> None:
    """Should return 404 Not found."""
    race_result_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundError(f"RaceResult with id {id} not found"),
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"races/{race.id}/race-results/{race_result_id}")
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 404 Not found."""
    race_result_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundError(f"RaceResult with id {id} not found"),
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=None,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(race_result.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.put(
            f"races/{race.id}/race-results/{race_result_id}",
            headers=headers,
            data=request_body,
        )
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
) -> None:
    """Should return 404 Not found."""
    race_result_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundError(f"RaceResult with id {id} not found"),
    )
    mocker.patch(
        "race_service.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
        return_value=None,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.delete(
            f"races/{race.id}/race-results/{race_result_id}", headers=headers
        )
        assert resp.status == HTTPStatus.NOT_FOUND
