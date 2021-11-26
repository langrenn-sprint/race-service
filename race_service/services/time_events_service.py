"""Module for time_events service."""
import logging
from typing import Any, List, Optional
import uuid

from race_service.adapters import TimeEventsAdapter
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


class TimeEventNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeEventsService:
    """Class representing a service for time_events."""

    @classmethod
    async def get_all_time_events(cls: Any, db: Any) -> List[TimeEvent]:
        """Get all time_events function."""
        time_events: List[TimeEvent] = []
        _time_events = await TimeEventsAdapter.get_all_time_events(db)
        for e in _time_events:
            time_events.append(TimeEvent.from_dict(e))
        return time_events

    @classmethod
    async def get_time_events_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List[TimeEvent]:
        """Get all time_events by event_id function."""
        time_events: List[TimeEvent] = []
        _time_events = await TimeEventsAdapter.get_time_events_by_event_id(db, event_id)
        for e in _time_events:
            time_events.append(TimeEvent.from_dict(e))
        return time_events

    @classmethod
    async def get_time_events_by_event_id_and_timing_point(
        cls: Any, db: Any, event_id: str, timing_point: str
    ) -> List[TimeEvent]:
        """Get all time_events by event_id and timing_point function."""
        time_events: List[TimeEvent] = []
        _time_events = (
            await TimeEventsAdapter.get_time_events_by_event_id_and_timing_point(
                db, event_id, timing_point
            )
        )
        for e in _time_events:
            time_events.append(TimeEvent.from_dict(e))
        return time_events

    @classmethod
    async def get_time_events_by_race_id(
        cls: Any, db: Any, race_id: str
    ) -> List[TimeEvent]:
        """Get all time_events by race_id function."""
        time_events: List[TimeEvent] = []
        _time_events = await TimeEventsAdapter.get_time_events_by_race_id(db, race_id)
        for e in _time_events:
            time_events.append(TimeEvent.from_dict(e))
        return time_events

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
        """
        logging.debug(f"trying to insert time_event: {time_event}")
        # Validation:
        await validate_time_event(db, time_event)
        if time_event.id:
            raise IllegalValueException("Cannot create time_event with input id.")
        # create ids:
        id = create_id()
        time_event.id = id
        # insert new time_event
        new_time_event = time_event.to_dict()
        logging.debug(f"new_time_event: {new_time_event}")
        result = await TimeEventsAdapter.create_time_event(db, new_time_event)
        logging.debug(f"inserted time_event with id: {id}")
        if result:
            return id
        raise CouldNotCreateTimeEventException(
            "Creation of time-event failed."
        ) from None

    @classmethod
    async def get_time_event_by_id(cls: Any, db: Any, id: str) -> TimeEvent:
        """Get time_event function."""
        time_event = await TimeEventsAdapter.get_time_event_by_id(db, id)
        # return the document if found:
        if time_event:
            return TimeEvent.from_dict(time_event)
        raise TimeEventNotFoundException(f"TimeEvent with id {id} not found")

    @classmethod
    async def update_time_event(
        cls: Any, db: Any, id: str, time_event: TimeEvent
    ) -> Optional[str]:
        """Get time_event function."""
        # get old document
        old_time_event = await TimeEventsAdapter.get_time_event_by_id(db, id)
        # update the time_event if found:
        if old_time_event:
            if time_event.id != old_time_event["id"]:
                raise IllegalValueException("Cannot change id for time_event.")
            new_time_event = time_event.to_dict()
            result = await TimeEventsAdapter.update_time_event(db, id, new_time_event)
            return result
        raise TimeEventNotFoundException(f"TimeEvent with id {id} not found.")

    @classmethod
    async def delete_time_event(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get time_event function."""
        # get old document
        time_event = await TimeEventsAdapter.get_time_event_by_id(db, id)
        # delete the document if found:
        if time_event:
            result = await TimeEventsAdapter.delete_time_event(db, id)
            return result
        raise TimeEventNotFoundException(f"TimeEvent with id {id} not found")


#   Validation:
async def validate_time_event(db: Any, time_event: TimeEvent) -> None:
    """Validate the time_event."""
    # TODO: validate time_event-properties.
    pass
