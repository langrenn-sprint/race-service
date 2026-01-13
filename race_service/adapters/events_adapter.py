"""Module for events adapter."""

import os
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

from aiohttp import ClientSession
from aiohttp.web import (
    HTTPInternalServerError,
)
from dotenv import load_dotenv

load_dotenv()

EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER", "events.example.com")
EVENTS_HOST_PORT = int(os.getenv("EVENTS_HOST_PORT", "8080"))
COMPETITION_FORMAT_HOST_SERVER = os.getenv(
    "COMPETITION_FORMAT_HOST_SERVER", "competition-format.example.com"
)
COMPETITION_FORMAT_HOST_PORT = int(os.getenv("COMPETITION_FORMAT_HOST_PORT", "8080"))


class EventNotFoundError(Exception):
    """Class representing custom exception for get method."""


class CompetitionFormatNotFoundError(Exception):
    """Class representing custom exception for get method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceclassesNotFoundError(Exception):
    """Class representing custom exception for get method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceclassNotFoundError(Exception):
    """Class representing custom exception for get method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantsNotFoundError(Exception):
    """Class representing custom exception for get method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class EventsAdapter:
    """Class representing an adapter for events."""

    @classmethod
    async def get_event_by_id(
        cls: Any, token: str, event_id: str
    ) -> dict:  # pragma: no cover
        """Get event from event-service."""
        del token  # for now we do not use token
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}"

        async with ClientSession() as session, session.get(url) as response:
            if response.status == HTTPStatus.OK:
                return await response.json()
            if response.status == HTTPStatus.NOT_FOUND:
                msg = f"Event {event_id} not found."
                raise EventNotFoundError(msg) from None
            raise HTTPInternalServerError(
                reason=f"Got unknown status from events service: {response.status}."
            ) from None

    @classmethod
    async def get_competition_format(
        cls: Any,
        token: str,
        event_id: str,
        competition_format_name: str | None = None,
    ) -> dict:  # pragma: no cover
        """Get competition_format from event-service."""
        async with ClientSession() as session:
            # First we try to get the competition-format from the event:
            url = (
                f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
                f"/events/{event_id}/format"
            )
            async with session.get(url) as response:
                if response.status == HTTPStatus.OK:
                    return await response.json()
                if response.status == HTTPStatus.NOT_FOUND:
                    pass  # We will try to get the global config
                else:
                    raise HTTPInternalServerError(
                        reason=(
                            "Got unknown status from events service"
                            f"when getting competition_format from event {event_id}/"
                            f"{competition_format_name}: {response.status}."
                        )
                    ) from None
            # We have not found event specific format, get the global config:
            if not competition_format_name:
                event = await cls.get_event_by_id(token, event_id)
                competition_format_name = event["competition_format"]
            url = (
                f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}"
                f"/competition-formats?name={competition_format_name}"
            )
            async with session.get(url) as response:
                if response.status == HTTPStatus.OK:
                    competition_formats = await response.json()
                    return competition_formats[0]
                if response.status == HTTPStatus.NOT_FOUND:
                    msg = f'CompetitionFormat "{competition_format_name!r}" not found.'
                    raise CompetitionFormatNotFoundError(msg) from None
                raise HTTPInternalServerError(
                    reason=(
                        "Got unknown status from events service"
                        f"when getting competition_format {competition_format_name}:"
                        f"{response.status}."
                    )
                ) from None

    @classmethod
    async def get_raceclasses(
        cls: Any, token: str, event_id: str
    ) -> list[dict]:  # pragma: no cover
        """Get raceclasses from event-service."""
        del token  # for now we do not use token
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/raceclasses"

        async with ClientSession() as session, session.get(url) as response:
            if response.status == HTTPStatus.OK:
                raceclasses = await response.json()
                if len(raceclasses) == 0:
                    msg = f"No raceclasses found for event {event_id}."
                    raise RaceclassesNotFoundError(msg)
                return raceclasses
            raise HTTPInternalServerError(
                reason=(
                    "Got unknown status from events service"
                    f"when getting raceclasses for event {event_id}:"
                    f"{response.status}."
                )
            ) from None

    @classmethod
    async def get_raceclass_by_name(
        cls: Any, token: str, event_id: str, name: str
    ) -> dict:  # pragma: no cover
        """Get a raceclass by name from event-service."""
        del token  # for now we do not use token
        url = (
            f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
            f"/events/{event_id}/raceclasses?name={quote(name)}"
        )

        async with ClientSession() as session, session.get(url) as response:
            if response.status == HTTPStatus.OK:
                raceclasses = await response.json()
                if len(raceclasses) == 0:
                    msg = f'Raceclass "{name}" not found for event {event_id}.'
                    raise RaceclassNotFoundError(msg)
                return raceclasses[0]
            raise HTTPInternalServerError(
                reason=(
                    "Got unknown status from events service "
                    f'when getting raceclass "{name}" for event {event_id}: '
                    f"{response.status}."
                )
            ) from None

    @classmethod
    async def get_contestants(
        cls: Any, token: str, event_id: str
    ) -> list[dict]:  # pragma: no cover
        """Get contestants from event-service."""
        del token  # for now we do not use token
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"

        async with ClientSession() as session, session.get(url) as response:
            if response.status == HTTPStatus.OK:
                contestants = await response.json()
                if len(contestants) == 0:
                    msg = f"No contestants found for event {event_id}."
                    raise ContestantsNotFoundError(msg)
                return contestants
            raise HTTPInternalServerError(
                reason=(
                    "Got unknown status from events service"
                    f"when getting contestants for event {event_id}:"
                    f"{response.status}."
                )
            ) from None
