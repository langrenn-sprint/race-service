"""Module for timeevents service."""
import logging
from typing import Any, List, Optional
import uuid

from race_service.adapters import TimeeventsAdapter
from race_service.models import Timeevent
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class TimeeventNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeeventsService:
    """Class representing a service for timeevents."""

    @classmethod
    async def get_all_timeevents(cls: Any, db: Any) -> List[Timeevent]:
        """Get all timeevents function."""
        timeevents: List[Timeevent] = []
        _timeevents = await TimeeventsAdapter.get_all_timeevents(db)
        for e in _timeevents:
            timeevents.append(Timeevent.from_dict(e))
        return timeevents

    @classmethod
    async def get_timeevents_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List[Timeevent]:
        """Get all timeevents by event_id function."""
        timeevents: List[Timeevent] = []
        _timeevents = await TimeeventsAdapter.get_timeevents_by_event_id(db, event_id)
        for e in _timeevents:
            timeevents.append(Timeevent.from_dict(e))
        return timeevents

    @classmethod
    async def create_timeevent(
        cls: Any, db: Any, timeevent: Timeevent
    ) -> Optional[str]:
        """Create timeevent function.

        Args:
            db (Any): the db
            timeevent (Timeevent): a timeevent instanse to be created

        Returns:
            Optional[str]: The id of the created timeevent. None otherwise.

        Raises:
            IllegalValueException: input object has illegal values
        """
        logging.debug(f"trying to insert timeevent: {timeevent}")
        # Validation:
        await validate_timeevent(db, timeevent)
        if timeevent.id:
            raise IllegalValueException("Cannot create timeevent with input id.")
        # create ids:
        id = create_id()
        timeevent.id = id
        # insert new timeevent
        new_timeevent = timeevent.to_dict()
        logging.debug(f"new_timeevent: {new_timeevent}")
        result = await TimeeventsAdapter.create_timeevent(db, new_timeevent)
        logging.debug(f"inserted timeevent with id: {id}")
        if result:
            return id
        return None

    @classmethod
    async def get_timeevent_by_id(cls: Any, db: Any, id: str) -> Timeevent:
        """Get timeevent function."""
        timeevent = await TimeeventsAdapter.get_timeevent_by_id(db, id)
        # return the document if found:
        if timeevent:
            return Timeevent.from_dict(timeevent)
        raise TimeeventNotFoundException(f"Timeevent with id {id} not found")

    @classmethod
    async def update_timeevent(
        cls: Any, db: Any, id: str, timeevent: Timeevent
    ) -> Optional[str]:
        """Get timeevent function."""
        # get old document
        old_timeevent = await TimeeventsAdapter.get_timeevent_by_id(db, id)
        # update the timeevent if found:
        if old_timeevent:
            if timeevent.id != old_timeevent["id"]:
                raise IllegalValueException("Cannot change id for timeevent.")
            new_timeevent = timeevent.to_dict()
            result = await TimeeventsAdapter.update_timeevent(db, id, new_timeevent)
            return result
        raise TimeeventNotFoundException(f"Timeevent with id {id} not found.")

    @classmethod
    async def delete_timeevent(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get timeevent function."""
        # get old document
        timeevent = await TimeeventsAdapter.get_timeevent_by_id(db, id)
        # delete the document if found:
        if timeevent:
            result = await TimeeventsAdapter.delete_timeevent(db, id)
            return result
        raise TimeeventNotFoundException(f"Timeevent with id {id} not found")


#   Validation:
async def validate_timeevent(db: Any, timeevent: Timeevent) -> None:
    """Validate the timeevent."""
    # TODO: validate timeevent-properties.
    pass
