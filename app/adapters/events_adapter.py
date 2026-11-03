"""Module for events adapter."""

import os
from http import HTTPStatus
from typing import Any
from uuid import UUID

from httpx import AsyncClient

EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER", "events.example.com")
EVENTS_HOST_PORT = int(os.getenv("EVENTS_HOST_PORT", "8080"))
COMPETITION_FORMAT_HOST_SERVER = os.getenv(
    "COMPETITION_FORMAT_HOST_SERVER", "competition-format.example.com"
)
COMPETITION_FORMAT_HOST_PORT = int(os.getenv("COMPETITION_FORMAT_HOST_PORT", "8080"))


class EventsAdapterError(Exception):
    """Class representing custom exception for unexpected responses."""


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


class ContestantsNotFoundError(Exception):
    """Class representing custom exception for get method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class EventsAdapter:
    """Class representing an adapter for events."""

    @classmethod
    async def get_event_by_id(cls: Any, event_id: UUID) -> dict:  # pragma: no cover
        """Get event from event-service."""
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}"

        async with AsyncClient() as client:
            response = await client.get(url)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        if response.status_code == HTTPStatus.NOT_FOUND:
            msg = f"Event {event_id} not found."
            raise EventNotFoundError(msg) from None
        msg = f"Got unknown status from events service: {response.status_code}."
        raise EventsAdapterError(msg) from None

    @classmethod
    async def get_competition_format(
        cls: Any,
        event_id: UUID,
        competition_format_name: str | None = None,
    ) -> dict:  # pragma: no cover
        """Get competition_format from event-service."""
        async with AsyncClient() as client:
            # First we try to get the competition-format from the event:
            url = (
                f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
                f"/events/{event_id}/format"
            )
            response = await client.get(url)
            if response.status_code == HTTPStatus.OK:
                return response.json()
            if response.status_code == HTTPStatus.NOT_FOUND:
                pass  # We will try to get the global config
            else:
                msg = (
                    "Got unknown status from events service"
                    f"when getting competition_format from event {event_id}/"
                    f"{competition_format_name}: {response.status_code}."
                )
                raise EventsAdapterError(msg) from None
            # We have not found event specific format, get the global config:
            if not competition_format_name:
                event = await cls.get_event_by_id(event_id)
                competition_format_name = event["competition_format"]
            url = (
                f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}"
                "/competition-formats"
            )
            response = await client.get(url, params={"name": competition_format_name})
            if response.status_code == HTTPStatus.OK:
                competition_formats = response.json()
                return competition_formats[0]
            if response.status_code == HTTPStatus.NOT_FOUND:
                msg = f'CompetitionFormat "{competition_format_name!r}" not found.'
                raise CompetitionFormatNotFoundError(msg) from None
            msg = (
                "Got unknown status from events service"
                f"when getting competition_format {competition_format_name}:"
                f"{response.status_code}."
            )
            raise EventsAdapterError(msg) from None

    @classmethod
    async def get_raceclasses(
        cls: Any, event_id: UUID
    ) -> list[dict]:  # pragma: no cover
        """Get raceclasses from event-service."""
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/raceclasses"

        async with AsyncClient() as client:
            response = await client.get(url)
        if response.status_code == HTTPStatus.OK:
            raceclasses = response.json()
            if len(raceclasses) == 0:
                msg = f"No raceclasses found for event {event_id}."
                raise RaceclassesNotFoundError(msg)
            return raceclasses
        msg = (
            "Got unknown status from events service"
            f"when getting raceclasses for event {event_id}:"
            f"{response.status_code}."
        )
        raise EventsAdapterError(msg) from None

    @classmethod
    async def get_contestants(
        cls: Any, event_id: UUID
    ) -> list[dict]:  # pragma: no cover
        """Get contestants from event-service."""
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"

        async with AsyncClient() as client:
            response = await client.get(url)
        if response.status_code == HTTPStatus.OK:
            contestants = response.json()
            if len(contestants) == 0:
                msg = f"No contestants found for event {event_id}."
                raise ContestantsNotFoundError(msg)
            return contestants
        msg = (
            "Got unknown status from events service"
            f"when getting contestants for event {event_id}:"
            f"{response.status_code}."
        )
        raise EventsAdapterError(msg) from None
