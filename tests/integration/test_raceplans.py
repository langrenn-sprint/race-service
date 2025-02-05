"""Integration test cases for the raceplans route."""

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

from race_service.adapters import RaceclassesNotFoundError, RaceplanNotFoundError
from race_service.models import IndividualSprintRace, IntervalStartRace, Raceplan

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


@pytest.fixture
async def event() -> dict[str, Any]:
    """An event object for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Oslo Skagen sprint",
        "competition_format": "Interval Start",
        "date_of_event": "2021-08-31",
        "time_of_event": "09:00:00",
        "organiser": "Lyn Ski",
        "webpage": "https://example.com",
        "information": "Testarr for å teste den nye løysinga.",
    }


@pytest.fixture
async def competition_format() -> dict[str, Any]:
    """A competition-format for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Individual Sprint",
        "starting_order": "Draw",
        "start_procedure": "Heat Start",
        "time_between_groups": "00:15:00",
        "time_between_rounds": "00:10:00",
        "time_between_heats": "00:02:30",
        "rounds_ranked_classes": ["Q", "S", "F"],
        "rounds_non_ranked_classes": ["R1", "R2"],
        "max_no_of_contestants_in_raceclass": 80,
        "max_no_of_contestants_in_race": 10,
        "datatype": "individual_sprint",
        "race_config_non_ranked": None,
        "race_config_ranked": None,
    }


@pytest.fixture
async def competition_format_interval_start() -> dict[str, Any]:
    """A competition-format for testing."""
    return {
        "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
        "name": "Interval Start",
        "start_procedure": "Interval Start",
        "time_between_groups": "00:10:00",
        "intervals": "00:00:30",
        "max_no_of_contestants_in_raceclass": 1000,
        "max_no_of_contestants_in_race": 1000,
    }


@pytest.fixture
async def raceclasses() -> list[dict[str, Any]]:
    """An raceclasses object for testing."""
    return [
        {
            "id": "190e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G15",
            "ageclasses": ["G 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 8,
            "ranking": True,
            "group": 1,
            "order": 2,
        },
        {
            "id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "G16",
            "ageclasses": ["G 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 8,
            "ranking": True,
            "group": 1,
            "order": 4,
        },
        {
            "id": "390e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J15",
            "ageclasses": ["J 15 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 8,
            "ranking": True,
            "group": 1,
            "order": 1,
        },
        {
            "id": "490e70d5-0933-4af0-bb53-1d705ba7eb95",
            "name": "J16",
            "ageclasses": ["J 16 år"],
            "event_id": "290e70d5-0933-4af0-bb53-1d705ba7eb95",
            "no_of_contestants": 8,
            "ranking": True,
            "group": 1,
            "order": 3,
        },
    ]


@pytest.fixture
async def interval_start_races(event: dict) -> list[IntervalStartRace]:
    """Create a a list of interval-start races."""
    return [
        IntervalStartRace(
            id="race_1",
            raceclass="G16",
            order=1,
            start_time=datetime.fromisoformat("2021-08-31 12:00:00"),
            no_of_contestants=8,
            max_no_of_contestants=10,
            event_id=event["id"],
            raceplan_id="",
            start_entries=[],
            results={},
            datatype="interval_start",
        ),
        IntervalStartRace(
            id="race_2",
            raceclass="G16",
            order=2,
            start_time=datetime.fromisoformat("2021-08-31 12:15:00"),
            no_of_contestants=8,
            max_no_of_contestants=10,
            event_id=event["id"],
            raceplan_id="",
            start_entries=[],
            results={},
            datatype="interval_start",
        ),
        IntervalStartRace(
            id="race_3",
            raceclass="G16",
            order=3,
            start_time=datetime.fromisoformat("2021-08-31 12:30:00"),
            no_of_contestants=8,
            max_no_of_contestants=10,
            event_id=event["id"],
            raceplan_id="",
            start_entries=[],
            results={},
            datatype="interval_start",
        ),
        IntervalStartRace(
            id="race_4",
            raceclass="G16",
            order=4,
            start_time=datetime.fromisoformat("2021-08-31 12:45:00"),
            no_of_contestants=8,
            max_no_of_contestants=10,
            event_id=event["id"],
            raceplan_id="",
            start_entries=[],
            results={},
            datatype="interval_start",
        ),
    ]


@pytest.fixture
async def new_raceplan_interval_start(
    event: dict, interval_start_races: list[IntervalStartRace]
) -> Raceplan:
    """Create a raceplan object."""
    return Raceplan(
        id="raceplan_1",
        event_id=event["id"],
        no_of_contestants=32,
        races=[race.id for race in interval_start_races],
    )


@pytest.fixture
async def raceplan_interval_start(
    event: dict, interval_start_races: list[IntervalStartRace]
) -> Raceplan:
    """Create a mock raceplan object."""
    return Raceplan(
        id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        event_id=event["id"],
        no_of_contestants=32,
        races=[race.id for race in interval_start_races],
    )


@pytest.fixture
async def individual_sprint_races(event: dict) -> list[IndividualSprintRace]:
    """Create a a list of individual sprint races."""
    return [
        IndividualSprintRace(
            id="race_1",
            raceclass="G16",
            order=1,
            round="Q",
            index="A",
            heat=1,
            start_time=datetime.fromisoformat("2021-08-31 12:00:00"),
            no_of_contestants=8,
            max_no_of_contestants=10,
            event_id=event["id"],
            raceplan_id="",
            start_entries=[],
            results={},
            datatype="individual_sprint",
        ),
        IndividualSprintRace(
            id="race_2",
            raceclass="G16",
            order=2,
            round="Q",
            index="A",
            heat=2,
            start_time=datetime.fromisoformat("2021-08-31 12:15:00"),
            no_of_contestants=8,
            max_no_of_contestants=10,
            event_id=event["id"],
            raceplan_id="",
            start_entries=[],
            results={},
            datatype="individual_sprint",
        ),
        IndividualSprintRace(
            id="race_3",
            raceclass="G16",
            order=3,
            round="Q",
            index="A",
            heat=3,
            start_time=datetime.fromisoformat("2021-08-31 12:30:00"),
            no_of_contestants=8,
            max_no_of_contestants=10,
            event_id=event["id"],
            raceplan_id="",
            start_entries=[],
            results={},
            datatype="individual_sprint",
        ),
        IndividualSprintRace(
            id="race_4",
            raceclass="G16",
            order=4,
            round="Q",
            index="A",
            heat=4,
            start_time=datetime.fromisoformat("2021-08-31 12:45:00"),
            no_of_contestants=8,
            max_no_of_contestants=10,
            event_id=event["id"],
            raceplan_id="",
            start_entries=[],
            results={},
            datatype="individual_sprint",
        ),
    ]


@pytest.fixture
async def new_raceplan_individual_sprint(
    event: dict, individual_sprint_races: list[IndividualSprintRace]
) -> Raceplan:
    """Create a mock raceplan object."""
    return Raceplan(
        event_id=event["id"],
        no_of_contestants=32,
        races=[race.id for race in individual_sprint_races],
    )


@pytest.fixture
async def raceplan_individual_sprint(
    event: dict, individual_sprint_races: list[IndividualSprintRace]
) -> Raceplan:
    """Create a mock raceplan object."""
    return Raceplan(
        id="290e70d5-0933-4af0-bb53-1d705ba7eb95",
        event_id=event["id"],
        no_of_contestants=32,
        races=[race.id for race in individual_sprint_races],
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_raceplan(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    new_raceplan_interval_start: Raceplan,
    raceplan_interval_start: Raceplan,
    interval_start_races: list[IntervalStartRace],
) -> None:
    """Should return 405 Method Not Allowed."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.services.raceplans_service.create_id",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.create_raceplan",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.create_race",
        side_effect=interval_start_races,
    )

    request_body = dumps(
        new_raceplan_interval_start, indent=4, sort_keys=True, default=str
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.post("/raceplans", headers=headers, data=request_body)
        assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_raceplan_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_interval_start: Raceplan,
    interval_start_races: list[IntervalStartRace],
) -> None:
    """Should return OK, and a body containing one raceplan."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=interval_start_races,
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/raceplans/{raceplan_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert body["id"] == raceplan_id
        assert body["event_id"] == raceplan_interval_start.event_id
        assert len(body["races"]) == len(raceplan_interval_start.races)
        for race in body["races"]:
            assert race["raceclass"]
            assert race["order"]
            assert race["start_time"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_raceplan(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: dict,
    raceplan_individual_sprint: Raceplan,
    individual_sprint_races: list[IndividualSprintRace],
) -> None:
    """Should return OK, and an empty list."""
    raceplan_id = raceplan_individual_sprint.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=individual_sprint_races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(f"/raceplans/{raceplan_id}/validate", headers=headers)
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert len(body) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_raceplan_interval_start(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format_interval_start: dict,
    raceclasses: dict,
    raceplan_interval_start: Raceplan,
    interval_start_races: list[IntervalStartRace],
) -> None:
    """Should return OK, and an empty list."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=interval_start_races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format_interval_start,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(f"/raceplans/{raceplan_id}/validate", headers=headers)
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert len(body) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_raceplan_race_has_no_contestants(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: dict,
    raceplan_individual_sprint: Raceplan,
    individual_sprint_races: list[IndividualSprintRace],
) -> None:
    """Should return OK, and an empty list."""
    raceplan_id = raceplan_individual_sprint.id
    races = deepcopy(individual_sprint_races)
    races[0].no_of_contestants = 0

    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(f"/raceplans/{raceplan_id}/validate", headers=headers)
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert len(body) == 2  # noqa: PLR2004
        assert "0" in body  # error on raceplan-result (key "0")
        assert len(body["0"]) == 1
        assert body["0"] == [
            "The sum of contestants in races (24) is not equal to the number of contestants in the raceplan (32)."
        ]
        assert "1" in body  # it is race with order 1 that has no contestants
        assert len(body["1"]) == 1
        assert body["1"] == ["Race has no contestants."]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_raceplan_race_no_chronological_time(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: dict,
    raceplan_individual_sprint: Raceplan,
    individual_sprint_races: list[IndividualSprintRace],
) -> None:
    """Should return OK, and an empty list."""
    raceplan_id = raceplan_individual_sprint.id
    races = deepcopy(individual_sprint_races)
    races[-1].start_time = races[0].start_time

    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(f"/raceplans/{raceplan_id}/validate", headers=headers)
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert len(body) == 1
        assert "4" in body  # it is race with order 4 that has wrong time
        assert len(body["4"]) == 1
        assert body["4"] == ["Start time is not in chronological order."]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_raceplan_race_has_no_contestants_and_faulty_time(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: dict,
    raceplan_individual_sprint: Raceplan,
    individual_sprint_races: list[IndividualSprintRace],
) -> None:
    """Should return OK, and an empty list."""
    raceplan_id = raceplan_individual_sprint.id
    races = deepcopy(individual_sprint_races)
    races[-1].no_of_contestants = 0
    races[-1].start_time = races[0].start_time

    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(f"/raceplans/{raceplan_id}/validate", headers=headers)
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert len(body) == 2  # noqa: PLR2004
        assert "0" in body  # error on raceplan-result (key "0")
        assert len(body["0"]) == 1
        assert body["0"] == [
            "The sum of contestants in races (24) is not equal to the number of contestants in the raceplan (32)."
        ]
        assert "4" in body  # it is race with order 4 that has no contestants
        assert len(body["4"]) == 2  # noqa: PLR2004
        assert body["4"] == [
            "Start time is not in chronological order.",
            "Race has no contestants.",
        ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_raceplan_contestants_not_equal_no_of_contestants_in_raceclasses(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: dict,
    raceplan_individual_sprint: Raceplan,
    individual_sprint_races: list[IndividualSprintRace],
) -> None:
    """Should return OK, and an empty list."""
    raceplan_id = raceplan_individual_sprint.id
    raceplan_individual_sprint_with_faulty_contestants = deepcopy(
        raceplan_individual_sprint
    )
    raceplan_individual_sprint_with_faulty_contestants.no_of_contestants = 30

    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_individual_sprint_with_faulty_contestants,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=individual_sprint_races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        return_value=raceclasses,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(f"/raceplans/{raceplan_id}/validate", headers=headers)
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is dict
        assert len(body) == 1
        assert "0" in body  # error on raceplan-result (key "0")
        assert len(body["0"]) == 2  # noqa: PLR2004
        assert body["0"] == [
            "The sum of contestants in races (32) is not equal to the number of contestants in the raceplan (30).",
            "Number of contestants in raceplan (30) is not equal to the number of contestants in the raceclasses (32).",
        ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_raceplans_by_event_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_interval_start: Raceplan,
) -> None:
    """Should return OK, and a body containing one raceplan."""
    event_id = raceplan_interval_start.event_id
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        side_effect=RaceplanNotFoundError(f"Raceplan with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/raceplans?eventId={event_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == raceplan_id
        assert body[0]["event_id"] == raceplan_interval_start.event_id
        assert len(body[0]["races"]) == len(raceplan_interval_start.races)
        for race_id in body[0]["races"]:
            assert race_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_raceplans_by_event_id_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_individual_sprint: Raceplan,
) -> None:
    """Should return OK, and a body containing one raceplan."""
    event_id = raceplan_individual_sprint.event_id
    raceplan_id = raceplan_individual_sprint.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        side_effect=RaceplanNotFoundError(f"Raceplan with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_individual_sprint],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/raceplans?eventId={event_id}")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) == 1
        assert body[0]["id"] == raceplan_id
        assert body[0]["event_id"] == raceplan_individual_sprint.event_id
        assert len(body[0]["races"]) == len(raceplan_individual_sprint.races)
        for race_id in body[0]["races"]:
            assert race_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_raceplan_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_interval_start: Raceplan,
    interval_start_races: list[IntervalStartRace],
) -> None:
    """Should return No Content."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=interval_start_races,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(
        raceplan_interval_start.to_dict(), indent=4, sort_keys=True, default=str
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"/raceplans/{raceplan_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.NO_CONTENT


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_raceplans(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_interval_start: Raceplan,
) -> None:
    """Should return OK and a valid json body."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_all_raceplans",
        return_value=[raceplan_interval_start],
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.get("/raceplans")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        raceplans = await resp.json()
        assert type(raceplans) is list
        assert len(raceplans) > 0
        assert raceplans[0]["id"] == raceplan_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_raceplans_individual_sprint(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_individual_sprint: Raceplan,
) -> None:
    """Should return OK and a valid json body."""
    raceplan_id = raceplan_individual_sprint.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_all_raceplans",
        return_value=[raceplan_individual_sprint],
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.get("/raceplans")
        assert resp.status == HTTPStatus.OK
        assert "application/json" in resp.headers[hdrs.CONTENT_TYPE]
        body = await resp.json()
        assert type(body) is list
        assert len(body) > 0
        assert body[0]["id"] == raceplan_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_raceplan_by_id(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_interval_start: Raceplan,
) -> None:
    """Should return No Content."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.delete_raceplan",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=raceplan_interval_start.races,
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.delete_race",
        return_value=None,
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.delete(f"/raceplans/{raceplan_id}", headers=headers)
        assert resp.status == HTTPStatus.NO_CONTENT


# Bad cases


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_raceplan_has_no_raceclasses(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    event: dict,
    competition_format: dict,
    raceclasses: dict,
    raceplan_individual_sprint: Raceplan,
    individual_sprint_races: list[IndividualSprintRace],
) -> None:
    """Should return 400 Bad request."""
    raceplan_id = raceplan_individual_sprint.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_individual_sprint,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )
    mocker.patch(
        "race_service.adapters.races_adapter.RacesAdapter.get_race_by_id",
        side_effect=individual_sprint_races,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_raceclasses",
        side_effect=RaceclassesNotFoundError(
            f"No raceclasses found for event {event['id']}."
        ),
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_event_by_id",
        return_value=event,
    )
    mocker.patch(
        "race_service.adapters.events_adapter.EventsAdapter.get_competition_format",
        return_value=competition_format,
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.post(f"/raceplans/{raceplan_id}/validate", headers=headers)
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_raceplan_by_id_missing_mandatory_property(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_interval_start: Raceplan,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = {"id": raceplan_id}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"/raceplans/{raceplan_id}", headers=headers, json=request_body
        )
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_raceplan_by_id_different_id_in_body(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_interval_start: Raceplan,
) -> None:
    """Should return 422 HTTPUnprocessableEntity."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    update_body = deepcopy(raceplan_interval_start)
    update_body.id = "different_id"
    request_body = dumps(update_body.to_dict(), indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.put(
            f"/raceplans/{raceplan_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.UNPROCESSABLE_ENTITY


# Unauthorized cases:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_raceplan_by_id_no_authorization(
    client: _TestClient,
    mocker: MockFixture,
    raceplan_interval_start: Raceplan,
) -> None:
    """Should return 401 Unauthorized."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(
        raceplan_interval_start.to_dict(), indent=4, sort_keys=True, default=str
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.put(
            f"/raceplans/{raceplan_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_raceplan_by_id_no_authorization(
    client: _TestClient,
    mocker: MockFixture,
    raceplan_interval_start: Raceplan,
) -> None:
    """Should return 401 Unauthorized."""
    raceplan_id = raceplan_interval_start.id
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.delete_raceplan",
        return_value=raceplan_id,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=401)

        resp = await client.delete(f"/raceplans/{raceplan_id}")
        assert resp.status == HTTPStatus.UNAUTHORIZED


# Forbidden:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_raceplan_insufficient_role(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_interval_start: Raceplan,
) -> None:
    """Should return 403 Forbidden."""
    raceplan_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        return_value=raceplan_interval_start,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=True,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[raceplan_interval_start],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(raceplan_interval_start, indent=4, sort_keys=True, default=str)

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=403)
        resp = await client.put(
            f"/raceplans/{raceplan_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.FORBIDDEN


# NOT FOUND CASES:


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_raceplan_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    raceplan_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        side_effect=RaceplanNotFoundError("Raceplan with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)

        resp = await client.get(f"/raceplans/{raceplan_id}")
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_raceplan_not_found(
    client: _TestClient,
    mocker: MockFixture,
    token: MockFixture,
    raceplan_interval_start: Raceplan,
) -> None:
    """Should return 404 Not found."""
    raceplan_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        side_effect=RaceplanNotFoundError(
            f"Raceplan with id {raceplan_interval_start.id} not found."
        ),
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.update_raceplan",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    headers = {
        hdrs.CONTENT_TYPE: "application/json",
        hdrs.AUTHORIZATION: f"Bearer {token}",
    }

    request_body = dumps(
        raceplan_interval_start.to_dict(), indent=4, sort_keys=True, default=str
    )

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.put(
            f"/raceplans/{raceplan_id}", headers=headers, data=request_body
        )
        assert resp.status == HTTPStatus.NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_raceplan_not_found(
    client: _TestClient, mocker: MockFixture, token: MockFixture
) -> None:
    """Should return 404 Not found."""
    raceplan_id = "does-not-exist"
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplan_by_id",
        side_effect=RaceplanNotFoundError("Raceplan with id {id} not found."),
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.delete_raceplan",
        return_value=None,
    )
    mocker.patch(
        "race_service.adapters.raceplans_adapter.RaceplansAdapter.get_raceplans_by_event_id",
        return_value=[],
    )

    headers = {hdrs.AUTHORIZATION: f"Bearer {token}"}

    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        m.post(f"http://{USERS_HOST_SERVER}:{USERS_HOST_PORT}/authorize", status=204)
        resp = await client.delete(f"/raceplans/{raceplan_id}", headers=headers)
        assert resp.status == HTTPStatus.NOT_FOUND
