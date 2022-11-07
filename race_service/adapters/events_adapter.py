"""Module for events adapter."""
import os
from typing import Any, List

from aiohttp import ClientSession
from aiohttp.web import (
    HTTPInternalServerError,
)


EVENTS_HOST_SERVER = os.getenv("EVENTS_HOST_SERVER")
EVENTS_HOST_PORT = os.getenv("EVENTS_HOST_PORT")
COMPETITION_FORMAT_HOST_SERVER = os.getenv("COMPETITION_FORMAT_HOST_SERVER")
COMPETITION_FORMAT_HOST_PORT = os.getenv("COMPETITION_FORMAT_HOST_PORT")


class EventNotFoundException(Exception):
    """Class representing custom exception for get method."""

    pass


class FormatConfigurationNotFoundException(Exception):
    """Class representing custom exception for get method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceclassesNotFoundException(Exception):
    """Class representing custom exception for get method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantsNotFoundException(Exception):
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
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}"

        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    event = await response.json()
                    return event
                elif response.status == 404:
                    raise EventNotFoundException(
                        f"Event {event_id} not found."
                    ) from None
                else:
                    raise HTTPInternalServerError(
                        reason=f"Got unknown status from events service: {response.status}."
                    ) from None

    @classmethod
    async def get_format_configuration(
        cls: Any, token: str, event_id: str, competition_format_name: str
    ) -> dict:  # pragma: no cover
        """Get format_configuration from event-service."""
        async with ClientSession() as session:
            # First we try to get the configuration from the event:
            url = (
                f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}"
                f"/events/{event_id}/format"
            )
            async with session.get(url) as response:
                if response.status == 200:
                    format_configuration = await response.json()
                    return format_configuration
                elif response.status == 404:
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
            url = (
                f"http://{COMPETITION_FORMAT_HOST_SERVER}:{COMPETITION_FORMAT_HOST_PORT}"
                f"/competition-formats?name={competition_format_name}"
            )
            async with session.get(url) as response:
                if response.status == 200:
                    format_configurations = await response.json()
                    return format_configurations[0]
                elif response.status == 404:
                    raise FormatConfigurationNotFoundException(
                        f'FormatConfiguration "{competition_format_name}" not found.'
                    ) from None
                else:
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
    ) -> List[dict]:  # pragma: no cover
        """Get raceclasses from event-service."""
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/raceclasses"

        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    raceclasses = await response.json()
                    if len(raceclasses) == 0:
                        raise RaceclassesNotFoundException(
                            f"No raceclasses found for event {event_id}."
                        )
                    return raceclasses
                else:
                    raise HTTPInternalServerError(
                        reason=(
                            "Got unknown status from events service"
                            f"when getting raceclasses for event {event_id}:"
                            f"{response.status}."
                        )
                    ) from None

    @classmethod
    async def get_contestants(
        cls: Any, token: str, event_id: str
    ) -> List[dict]:  # pragma: no cover
        """Get contestants from event-service."""
        url = f"http://{EVENTS_HOST_SERVER}:{EVENTS_HOST_PORT}/events/{event_id}/contestants"

        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    contestants = await response.json()
                    if len(contestants) == 0:
                        raise ContestantsNotFoundException(
                            f"No contestants found for event {event_id}."
                        )
                    return contestants
                else:
                    raise HTTPInternalServerError(
                        reason=(
                            "Got unknown status from events service"
                            f"when getting contestants for event {event_id}:"
                            f"{response.status}."
                        )
                    ) from None
