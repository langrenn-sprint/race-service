"""Integration test cases for the race_results route."""

import os
import uuid
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from json import dumps

import jwt
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app.adapters import RaceNotFoundError, RaceResultNotFoundError
from app.models import Changelog, IndividualSprintRace, RaceResult, TimeEvent


@pytest.fixture
def token() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {
        "username": os.getenv("ADMIN_USERNAME"),
        "exp": 9999999999,
        "role": "admin",
    }
    return jwt.encode(payload, secret, algorithm)


@pytest.fixture
def token_unsufficient_role() -> str:
    """Create a valid token."""
    secret = os.getenv("JWT_SECRET")
    algorithm = "HS256"
    payload = {"username": "user", "exp": 9999999999, "role": "user"}
    return jwt.encode(payload, secret, algorithm)


TIME_EVENTS: list[TimeEvent] = [
    TimeEvent(
        id="1ba641c0-ed88-5934-9b13-667d34430228",
        bib=1,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        timing_point="Finish",
        rank=1,
        registration_time=datetime.fromisoformat("2023-02-11T12:01:02"),
        next_race="semi_name1",
        next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
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
        id="5c369f7a-1967-5a65-91da-2f6f99e3e86d",
        bib=2,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        timing_point="Finish",
        rank=2,
        registration_time=datetime.fromisoformat("2023-02-11T12:02:02"),
        next_race="semi_name1",
        next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
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
        id="913e08c2-5693-5900-b3e4-b3bd0acef11e",
        bib=2,
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        name="Petter Propell",
        club="Barnehagen",
        race="race_name",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        timing_point="Template",
        rank=2,
        registration_time=datetime.fromisoformat("2023-02-11T12:02:02"),
        next_race="semi_name1",
        next_race_id="c8a5e246-689d-5126-8b52-d4f6d373733b",
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
        id="50b75bea-866a-50fc-bde0-78cc68b04fec",
        race_id="f910dc1f-18da-50b1-948b-c847165a0556",
        timing_point="Finish",
        no_of_contestants=2,
        ranking_sequence=[
            "1ba641c0-ed88-5934-9b13-667d34430228",
            "5c369f7a-1967-5a65-91da-2f6f99e3e86d",
        ],
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
        event_id="e726010d-728b-5516-a930-dd8e9b210255",
        raceplan_id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        start_entries=[
            "f23c88f5-c6c9-5056-8c39-232a7a3fbd06",
            "5152cfad-4307-565b-8e66-e81f02d8d4e3",
            "1ad29a99-3e56-55e9-9a5d-2e8ffe7ae0a3",
            "7cd7988c-3eaa-5d1e-9b9d-8e3ed845cd34",
            "91547337-a276-5407-962e-a591c95b0478",
            "35106e04-9f97-5e62-a112-fbfd7cc6924b",
            "de5ab9f6-ddcd-57d3-bc3f-e05c1d37b54d",
            "6f733e30-ea78-54c1-b6aa-c86a1f0c675b",
        ],
        results={"Finish": "50b75bea-866a-50fc-bde0-78cc68b04fec"},
        round="Q",
        index="",
        heat=1,
        rule={"S": {"A": 5, "C": 0}, "F": {"C": "REST"}},
        datatype="individual_sprint",
    )


def get_time_event_by_id(id_: str) -> TimeEvent:
    """Mock function to look up correct time-event from list."""
    return next(
        time_event for time_event in TIME_EVENTS if str(time_event.id) == str(id_)
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_race_result(
    client: TestClient,
    token: MockFixture,
) -> None:
    """Should return 405 Not allowed."""
    request_body = dumps({}, indent=4, sort_keys=True, default=str)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    resp = client.post("races/1/race-results", headers=headers, content=request_body)
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_result_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return OK, and a body containing one race_result."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    resp = client.get(f"races/{race.id}/race-results/{race_result_id}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    body = resp.json()
    assert type(body) is dict
    assert body["id"] == str(race_result_id)
    assert body["race_id"] == str(race_result.race_id)
    assert body["timing_point"] == race_result.timing_point
    assert body["no_of_contestants"] == race_result.no_of_contestants
    assert "ranking_sequence" in body
    assert type(body["ranking_sequence"]) is list
    assert (
        len(body["ranking_sequence"]) == len(TIME_EVENTS) - 1
    )  # Template should not be included
    for time_event in body["ranking_sequence"]:
        assert type(time_event) is dict
        expected_time_event = get_time_event_by_id(id_=time_event["id"])
        assert time_event == expected_time_event.model_dump(mode="json")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_by_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return No Content."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        race_result.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"races/{race.id}/race-results/{race_result_id}",
        headers=headers,
        content=request_body,
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_results_by_race_id(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return OK and a valid json body."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    resp = client.get(f"races/{race.id}/race-results")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    race_results = resp.json()
    assert type(race_results) is list
    assert len(race_results) > 0
    assert race_results[0]["id"] == str(race_result_id)
    for time_event in race_results[0]["ranking_sequence"]:
        assert type(time_event) is dict
        expected_time_event = get_time_event_by_id(id_=time_event["id"])
        assert time_event == expected_time_event.model_dump(mode="json")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_results_by_race_id_idsonly(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return OK and a valid json body."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    resp = client.get(f"races/{race.id}/race-results?idsOnly=true")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    race_results = resp.json()
    assert type(race_results) is list
    assert len(race_results) > 0
    assert race_results[0]["id"] == str(race_result_id)
    for time_event in race_results[0]["ranking_sequence"]:
        assert type(time_event) is str
        expected_time_event = get_time_event_by_id(id_=time_event)
        assert time_event == str(expected_time_event.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_results_by_race_id_and_timing_point(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return OK and a valid json body."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_results_by_race_id_and_timing_point",
        return_value=[race_result],
    )
    mocker.patch(
        "app.adapters.time_events_adapter.TimeEventsAdapter.get_time_event_by_id",
        side_effect=get_time_event_by_id,
    )

    resp = client.get(f"races/{race.id}/race-results?timingPoint={'Finish'}")
    assert resp.status_code == HTTPStatus.OK
    assert "application/json" in resp.headers["Content-Type"]
    race_results = resp.json()
    assert type(race_results) is list
    assert len(race_results) == 1
    assert "Finish" in race.results
    assert race_results[0]["id"] == str(race_result_id)
    for time_event in race_results[0]["ranking_sequence"]:
        assert type(time_event) is dict
        expected_time_event = get_time_event_by_id(id_=time_event["id"])
        assert time_event == expected_time_event.model_dump(mode="json")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return No Content."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        return_value=race,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(
        f"races/{race.id}/race-results/{race_result_id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NO_CONTENT


# Bad cases


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_by_id_missing_mandatory_property(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = {"id": str(race_result_id)}

    resp = client.put(
        f"races/{race.id}/race-results/{race_result_id}",
        headers=headers,
        json=request_body,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_by_id_different_id_in_body(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    update_body = deepcopy(race_result)
    update_body.id = uuid.UUID("2b920f5c-eb82-5655-bd13-2001e5f0683e")
    request_body = dumps(
        update_body.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"races/{race.id}/race-results/{race_result_id}",
        headers=headers,
        content=request_body,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result_race_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 404 Not found."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
        return_value=True,
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=RaceNotFoundError(f"Race with id {race.id} not found."),
    )
    mocker.patch(
        "app.adapters.races_adapter.RacesAdapter.update_race",
        return_value=True,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(
        f"races/{race.id}/race-results/{race_result_id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND
    body = resp.json()
    assert "DB is inconsistent: cannot find race" in body["detail"]


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_by_id_no_authorization(
    client: TestClient,
    mocker: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 401 Unauthorized."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        return_value=race_result,
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=race_result_id,
    )

    headers = {"Content-Type": "application/json"}

    request_body = dumps(
        race_result.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"races/{race.id}/race-results/{race_result_id}",
        headers=headers,
        content=request_body,
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result_by_id_no_authorization(
    client: TestClient,
    mocker: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 401 Unauthorized."""
    race_result_id = race_result.id
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundError(f"RaceResult with id {id} not found"),
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
        return_value=race_result_id,
    )

    resp = client.delete(f"races/{race.id}/race-results/{race_result_id}")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


# Forbidden:


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_race_result_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
) -> None:
    """Should return 404 Not found."""
    race_result_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundError(f"RaceResult with id {id} not found"),
    )

    resp = client.get(f"races/{race.id}/race-results/{race_result_id}")
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_race_result_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
    race_result: RaceResult,
) -> None:
    """Should return 404 Not found."""
    race_result_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundError(f"RaceResult with id {id} not found"),
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.update_race_result",
        return_value=None,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    request_body = dumps(
        race_result.model_dump(mode="json"), indent=4, sort_keys=True, default=str
    )

    resp = client.put(
        f"races/{race.id}/race-results/{race_result_id}",
        headers=headers,
        content=request_body,
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_race_result_not_found(
    client: TestClient,
    mocker: MockFixture,
    token: MockFixture,
    race: IndividualSprintRace,
) -> None:
    """Should return 404 Not found."""
    race_result_id = "c644a3f6-b351-595b-beca-813a3b77a7f7"
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.get_race_result_by_id",
        side_effect=RaceResultNotFoundError(f"RaceResult with id {id} not found"),
    )
    mocker.patch(
        "app.adapters.race_results_adapter.RaceResultsAdapter.delete_race_result",
        return_value=None,
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(
        f"races/{race.id}/race-results/{race_result_id}", headers=headers
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND
