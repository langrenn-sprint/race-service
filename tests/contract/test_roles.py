"""Contract test cases for the role model (event-service-gui#215).

Users with each role are created in user-service and log in, so the tests use
real tokens with the role names user-service hands out. The tests check the
whole role model against the running service, and the raceday scenarios with
real data:
- contestant-admin adds and changes a late entry, but may not delete it.
- result-admin registers time events and removes a start entry.
- event-admin and result-admin may update race-results.
"""

import json
import logging
import os
import re
from collections.abc import AsyncGenerator
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import motor.motor_asyncio
import pytest
from httpx import AsyncClient, Response

from app.utils import db_utils
from tests.role_model import (
    ADMIN,
    CONTESTANT_ADMIN,
    EVENT_ADMIN,
    RESULT_ADMIN,
    ROLES,
    access_cases,
)

from .utils import _decide_group_order_and_ranking

DB_NAME = os.getenv("DB_NAME", "races_test")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
FILES = Path("tests/files")

logger = logging.getLogger(__name__)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _check(response: Response, expected: HTTPStatus, action: str) -> Response:
    assert response.status_code == expected, (
        f"{action}: got {response.status_code}, {response.text[:500]}"
    )
    return response


async def _login(
    client: AsyncClient, users_url: str, username: str, password: str
) -> str:
    response = await client.post(
        f"{users_url}/login", json={"username": username, "password": password}
    )
    return _check(response, HTTPStatus.OK, f"login {username}").json()["token"]


@pytest.fixture(scope="module", autouse=True)
async def clear_db(db_address: dict[str, Any]) -> AsyncGenerator:
    """Clear db before and after tests."""
    mongo = motor.motor_asyncio.AsyncIOMotorClient(
        **db_address, username=DB_USER, password=DB_PASSWORD
    )
    await db_utils.drop_db_and_recreate_indexes(mongo, DB_NAME)
    yield
    await db_utils.drop_db(mongo, DB_NAME)


@pytest.fixture(scope="module")
async def tokens(http_service: Any, users_url: str, clear_db: Any) -> dict[str, str]:
    """Log in as admin, create a user for each other role, and log in as them."""
    _ = http_service, clear_db  # the service is up, and the db is cleared first
    async with AsyncClient() as client:
        admin_token = await _login(
            client,
            users_url,
            os.environ["ADMIN_USERNAME"],
            os.environ["ADMIN_PASSWORD"],
        )
        tokens = {ADMIN: admin_token}
        for role in ROLES:
            if role == ADMIN:
                continue
            username = f"{role}@example.com"
            response = await client.post(
                f"{users_url}/users",
                headers=_auth(admin_token),
                json={"username": username, "password": "secret", "role": role},
            )
            _check(response, HTTPStatus.CREATED, f"create user with role {role}")
            tokens[role] = await _login(client, users_url, username, "secret")
    return tokens


@pytest.fixture(scope="module")
async def context(
    http_service: str,
    tokens: dict[str, str],
    competition_format_url: str,
    events_url: str,
) -> dict[str, Any]:
    """Set up an event with raceplan and startlist, as admin."""
    headers = _auth(tokens[ADMIN])
    async with AsyncClient() as client:
        response = await client.post(
            f"{competition_format_url}/competition-formats",
            headers=headers,
            json=json.loads(
                (FILES / "competition_format_individual_sprint.json").read_text()
            ),
        )
        _check(response, HTTPStatus.CREATED, "create competition format")

        response = await client.post(
            f"{events_url}/events",
            headers=headers,
            json=json.loads((FILES / "event_individual_sprint.json").read_text()),
        )
        _check(response, HTTPStatus.CREATED, "create event")
        event_id = response.headers["Location"].split("/")[-1]

        with (FILES / "contestants_all.csv").open("rb") as file:
            response = await client.post(
                f"{events_url}/events/{event_id}/contestants/file",
                headers=headers,
                files={"file": (file.name, file, "text/csv")},
            )
        _check(response, HTTPStatus.OK, "add contestants")

        response = await client.post(
            f"{events_url}/events/{event_id}/generate-raceclasses", headers=headers
        )
        _check(response, HTTPStatus.CREATED, "generate raceclasses")
        url = f"{events_url}/events/{event_id}/raceclasses"
        for raceclass in (await client.get(url)).json():
            (
                raceclass["group"],
                raceclass["order"],
                raceclass["ranking"],
            ) = await _decide_group_order_and_ranking(raceclass)
            response = await client.put(
                f"{url}/{raceclass['id']}", headers=headers, json=raceclass
            )
            _check(response, HTTPStatus.NO_CONTENT, "update raceclass")

        response = await client.post(
            f"{events_url}/events/{event_id}/contestants/assign-bibs", headers=headers
        )
        _check(response, HTTPStatus.CREATED, "assign bibs")

        for command in (
            "raceplans/generate-raceplan-for-event",
            "startlists/generate-startlist-for-event",
        ):
            response = await client.post(
                f"{http_service}/{command}",
                headers=headers,
                json={"event_id": event_id},
            )
            _check(response, HTTPStatus.CREATED, command)
        startlist_id = response.headers["Location"].split("/")[-1]

        response = await client.get(f"{http_service}/races?eventId={event_id}")
        race = _check(response, HTTPStatus.OK, "get races").json()[0]

    return {"event_id": event_id, "startlist_id": startlist_id, "race": race}


async def _add_late_entry(
    client: AsyncClient, http_service: str, context: dict, token: str, bib: int
) -> str:
    """Add a start entry to a race with room for it, and return its URL."""
    url = f"{http_service}/races?eventId={context['event_id']}"
    races = _check(await client.get(url), HTTPStatus.OK, "get races").json()
    race = next(
        race
        for race in races
        if len(race["start_entries"]) < race["max_no_of_contestants"]
    )
    entry = {
        "startlist_id": context["startlist_id"],
        "race_id": race["id"],
        "bib": bib,
        "starting_position": len(race["start_entries"]) + 1,
        "scheduled_start_time": race["start_time"],
        "name": "Sen Løper",
        "club": "Alltid sent ute IL",
    }
    response = await client.post(
        f"{http_service}/races/{race['id']}/start-entries",
        headers=_auth(token),
        json=entry,
    )
    _check(response, HTTPStatus.CREATED, "add late entry")
    # Location is an absolute URL with the service's own host name:
    return http_service + urlparse(response.headers["Location"]).path


# --- The role model, with real tokens -------------------------------------------


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
@pytest.mark.parametrize(("method", "path", "role", "allowed"), access_cases(ROLES))
async def test_write_access(
    http_service: str,
    tokens: dict[str, str],
    method: str,
    path: str,
    role: str,
    *,
    allowed: bool,
) -> None:
    """Allowed roles pass the role check, the others get 403.

    The role check runs before validation, so with an invalid id and an empty
    body an allowed role gets 422 and nothing is changed.
    """
    url = http_service + re.sub(r"\{\w+\}", "not-a-uuid", path)
    async with AsyncClient() as client:
        response = await client.request(
            method,
            url,
            headers=_auth(tokens[role]),
            json=None if method == "DELETE" else {},
        )
    expected = HTTPStatus.UNPROCESSABLE_ENTITY if allowed else HTTPStatus.FORBIDDEN
    _check(response, expected, f"{method} {path} as {role}")


# --- Raceday scenarios ----------------------------------------------------------


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_contestant_admin_late_entry(
    http_service: str, tokens: dict[str, str], context: dict
) -> None:
    """contestant-admin adds and changes a late entry, but may not delete it."""
    token = tokens[CONTESTANT_ADMIN]
    async with AsyncClient() as client:
        url = await _add_late_entry(client, http_service, context, token, bib=9001)

        entry = _check(await client.get(url), HTTPStatus.OK, "get entry").json()
        entry["name"] = "Sen Løper Endret"
        response = await client.put(url, headers=_auth(token), json=entry)
        _check(response, HTTPStatus.NO_CONTENT, "update late entry")

        response = await client.delete(url, headers=_auth(token))
        _check(response, HTTPStatus.FORBIDDEN, "delete as contestant-admin")

        entry = _check(await client.get(url), HTTPStatus.OK, "get entry").json()
        assert entry["name"] == "Sen Løper Endret"


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
@pytest.mark.parametrize("role", [RESULT_ADMIN, EVENT_ADMIN])
async def test_remove_start_entry(
    http_service: str, tokens: dict[str, str], context: dict, role: str
) -> None:
    """result-admin and event-admin may remove a start entry on raceday."""
    bib = {RESULT_ADMIN: 9002, EVENT_ADMIN: 9003}[role]
    async with AsyncClient() as client:
        url = await _add_late_entry(
            client, http_service, context, tokens[CONTESTANT_ADMIN], bib=bib
        )
        response = await client.delete(url, headers=_auth(tokens[role]))
        _check(response, HTTPStatus.NO_CONTENT, f"delete entry as {role}")
        _check(await client.get(url), HTTPStatus.NOT_FOUND, "get deleted entry")


@pytest.mark.contract
@pytest.mark.asyncio(scope="module")
async def test_time_events_and_race_results(
    http_service: str, tokens: dict[str, str], context: dict
) -> None:
    """result-admin registers a time event, and race-results can be updated.

    contestant-admin may do neither.
    """
    race = context["race"]
    async with AsyncClient() as client:
        url = f"{http_service}/races/{race['id']}/start-entries"
        bib = _check(await client.get(url), HTTPStatus.OK, "get entries").json()[0][
            "bib"
        ]
        time_event = {
            "bib": bib,
            "event_id": context["event_id"],
            "race_id": race["id"],
            "timing_point": "Finish",
            "registration_time": "2023-02-11T12:01:02",
            "status": "OK",
        }
        response = await client.post(
            f"{http_service}/time-events",
            headers=_auth(tokens[CONTESTANT_ADMIN]),
            json=time_event,
        )
        _check(response, HTTPStatus.FORBIDDEN, "time event as contestant-admin")
        response = await client.post(
            f"{http_service}/time-events",
            headers=_auth(tokens[RESULT_ADMIN]),
            json=time_event,
        )
        _check(response, HTTPStatus.OK, "time event as result-admin")

        url = f"{http_service}/races/{race['id']}/race-results?idsOnly=true"
        race_result = _check(
            await client.get(url), HTTPStatus.OK, "get race-results"
        ).json()[0]
        url = f"{http_service}/races/{race['id']}/race-results/{race_result['id']}"
        for role, expected in [
            (CONTESTANT_ADMIN, HTTPStatus.FORBIDDEN),
            (EVENT_ADMIN, HTTPStatus.NO_CONTENT),
            (RESULT_ADMIN, HTTPStatus.NO_CONTENT),
        ]:
            response = await client.put(
                url, headers=_auth(tokens[role]), json=race_result
            )
            _check(response, expected, f"update race-result as {role}")
