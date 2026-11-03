"""Module for time_events service."""

import logging
from typing import Any
from uuid import UUID

from app.adapters import (
    TimeEventNotFoundError,
    TimeEventsAdapter,
)
from app.models import TimeEvent
from app.services import IllegalValueError


class CouldNotCreateTimeEventError(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeEventAllreadyExistError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeEventsService:
    """Class representing a service for time_events."""

    logger = logging.getLogger(
        "race_service.services.time_events_service.TimeEventsService"
    )

    @classmethod
    async def create_time_event(cls: Any, time_event: TimeEvent) -> UUID:
        """Create time_event function.

        Args:
            time_event (TimeEvent): a time_event instanse to be created

        Returns:
            UUID: The id of the created time_event. None otherwise.

        Raises:
            CouldNotCreateTimeEventError: creation failed
            TimeEventAllreadyExistError: time_event for bib and given timing-point already exists
        """
        cls.logger.debug(f"trying to insert time_event: {time_event}")
        # Validation:
        await validate_time_event(time_event)
        # If time-event for bib and given timing-point already exists in the race, throw error:
        _time_events = await TimeEventsAdapter.get_time_events_by_race_id(
            time_event.race_id,  # ty: ignore[invalid-argument-type]
        )
        for _time_event in _time_events:
            if (
                _time_event.timing_point != "Template"
                and _time_event.bib == time_event.bib
                and _time_event.timing_point == time_event.timing_point
            ):
                msg = (
                    f"Time-event for bib {time_event.bib} and timing-point {time_event.timing_point}"
                    f" already exists in race {time_event.race_id}."
                )
                raise TimeEventAllreadyExistError(msg)
        # insert new time_event
        cls.logger.debug(f"new time_event: {time_event}")
        result = await TimeEventsAdapter.create_time_event(time_event)
        cls.logger.debug(f"inserted time_event with id: {time_event.id}")
        if result:
            return time_event.id
        msg = "Creation of time-event failed."
        raise CouldNotCreateTimeEventError(msg) from None

    @classmethod
    async def update_time_event(
        cls: Any, id_: UUID, time_event: TimeEvent
    ) -> str | None:
        """Get time_event function."""
        # get old document
        try:
            old_time_event = await TimeEventsAdapter.get_time_event_by_id(id_)
        except TimeEventNotFoundError as e:
            msg = f"TimeEvent with id {id_} not found."
            raise TimeEventNotFoundError(msg) from e
        # update the time_event if found:
        if time_event.id != old_time_event.id:
            msg = "Cannot change id for time_event."
            raise IllegalValueError(msg)
        return await TimeEventsAdapter.update_time_event(id_, time_event)

    @classmethod
    async def delete_time_event(cls: Any, id_: UUID) -> str | None:
        """Get time_event function."""
        # check if time-event exist:
        try:
            await TimeEventsAdapter.get_time_event_by_id(id_)
        except TimeEventNotFoundError as e:
            msg = f"TimeEvent with id {id_} not found."
            raise TimeEventNotFoundError(msg) from e
        # delete the document if found:
        return await TimeEventsAdapter.delete_time_event(id_)


#   Validation:
async def validate_time_event(time_event: TimeEvent) -> None:
    """Validate the time_event."""
