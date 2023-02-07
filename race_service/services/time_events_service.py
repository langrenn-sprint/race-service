"""Module for time_events service."""
import logging
from typing import Any, Optional
import uuid

from race_service.adapters import TimeEventNotFoundException, TimeEventsAdapter
from race_service.models import TimeEvent
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class CouldNotCreateTimeEventException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeEventAllreadyExistException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeEventsService:
    """Class representing a service for time_events."""

    @classmethod
    async def create_time_event(cls: Any, db: Any, time_event: TimeEvent) -> str:
        """Create time_event function.

        Args:
            db (Any): the db
            time_event (TimeEvent): a time_event instanse to be created

        Returns:
            str: The id of the created time_event. None otherwise.

        Raises:
            CouldNotCreateTimeEventException: creation failed
            IllegalValueException: input object has illegal values
            TimeEventAllreadyExistException: time_event for bib and given timing-point already exists
        """
        logging.debug(f"trying to insert time_event: {time_event}")
        # Validation:
        await validate_time_event(db, time_event)
        if time_event.id:
            raise IllegalValueException("Cannot create time_event with input id.")
        # If time-event for bib and given timing-point already exists in the race, throw error:
        _time_events = await TimeEventsAdapter.get_time_events_by_race_id(
            db, time_event.race_id  # type: ignore
        )
        for _time_event in _time_events:
            if _time_event.timing_point != "Template":
                if (
                    _time_event.bib == time_event.bib
                    and _time_event.timing_point == time_event.timing_point
                ):
                    raise TimeEventAllreadyExistException(
                        (
                            f"Time-event for bib {time_event.bib} and timing-point {time_event.timing_point}"
                            f" already exists in race {time_event.race_id}."
                        )
                    )
        # create ids:
        id = create_id()
        time_event.id = id
        # insert new time_event
        logging.debug(f"new time_event: {time_event}")
        result = await TimeEventsAdapter.create_time_event(db, time_event)
        logging.debug(f"inserted time_event with id: {id}")
        if result:
            return id
        raise CouldNotCreateTimeEventException(
            "Creation of time-event failed."
        ) from None

    @classmethod
    async def update_time_event(
        cls: Any, db: Any, id: str, time_event: TimeEvent
    ) -> Optional[str]:
        """Get time_event function."""
        # get old document
        try:
            old_time_event = await TimeEventsAdapter.get_time_event_by_id(db, id)
        except TimeEventNotFoundException as e:
            raise TimeEventNotFoundException(
                f"TimeEvent with id {id} not found."
            ) from e
        # update the time_event if found:
        if time_event.id != old_time_event.id:
            raise IllegalValueException("Cannot change id for time_event.")
        result = await TimeEventsAdapter.update_time_event(db, id, time_event)
        return result

    @classmethod
    async def delete_time_event(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get time_event function."""
        # check if time-event exist:
        try:
            await TimeEventsAdapter.get_time_event_by_id(db, id)
        except TimeEventNotFoundException as e:
            raise TimeEventNotFoundException(
                f"TimeEvent with id {id} not found."
            ) from e
        # delete the document if found:
        result = await TimeEventsAdapter.delete_time_event(db, id)
        return result


#   Validation:
async def validate_time_event(db: Any, time_event: TimeEvent) -> None:
    """Validate the time_event."""
    # TODO: validate time_event-properties.
    pass
