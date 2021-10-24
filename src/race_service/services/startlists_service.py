"""Module for startlists service."""
import logging
from typing import Any, List, Optional
import uuid

from race_service.adapters import StartlistsAdapter
from race_service.models import Startlist
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class StartlistNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartlistAllreadyExistException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartlistsService:
    """Class representing a service for startlists."""

    @classmethod
    async def get_all_startlists(cls: Any, db: Any) -> List[Startlist]:
        """Get all startlists function."""
        startlists: List[Startlist] = []
        _startlists = await StartlistsAdapter.get_all_startlists(db)
        if _startlists:
            for _s in _startlists:
                startlists.append(Startlist.from_dict(_s))
        return startlists

    @classmethod
    async def get_startlist_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List[Startlist]:
        """Get all startlists by event_id function."""
        startlists: List[Startlist] = []
        _startlists = await StartlistsAdapter.get_startlist_by_event_id(db, event_id)
        if _startlists:
            for _s in _startlists:
                startlists.append(Startlist.from_dict(_s))
        return startlists

    @classmethod
    async def create_startlist(
        cls: Any, db: Any, startlist: Startlist
    ) -> Optional[str]:
        """Create startlist function.

        Args:
            db (Any): the db
            startlist (Startlist): a startlist instanse to be created

        Returns:
            Optional[str]: The id of the created startlist. None otherwise.

        Raises:
            IllegalValueException: input object has illegal values
            StartlistAllreadyExistException: event can have zero or one plan
        """
        logging.debug(f"trying to insert startlist: {startlist}")
        # Event can have one, and only, one startlist:
        existing_sl = await StartlistsAdapter.get_startlist_by_event_id(
            db, startlist.event_id
        )
        if existing_sl and len(existing_sl) > 0:
            raise StartlistAllreadyExistException(
                f'Event "{startlist.event_id}" already has a startlist.'
            )
        # Validation:
        await validate_startlist(db, startlist)
        if startlist.id:
            raise IllegalValueException("Cannot create startlist with input id.")
        # create ids:
        id = create_id()
        startlist.id = id
        for start_event in startlist.start_events:
            start_event.id = create_id()
        # insert new startlist
        new_startlist = startlist.to_dict()
        logging.debug(f"new_startlist: {new_startlist}")
        result = await StartlistsAdapter.create_startlist(db, new_startlist)
        logging.debug(f"inserted startlist with id: {id}")
        if result:
            return id
        return None

    @classmethod
    async def get_startlist_by_id(cls: Any, db: Any, id: str) -> Startlist:
        """Get startlist function."""
        startlist = await StartlistsAdapter.get_startlist_by_id(db, id)
        # return the document if found:
        if startlist:
            return Startlist.from_dict(startlist)
        raise StartlistNotFoundException(f"Startlist with id {id} not found")

    @classmethod
    async def update_startlist(
        cls: Any, db: Any, id: str, startlist: Startlist
    ) -> Optional[str]:
        """Get startlist function."""
        # get old document
        old_startlist = await StartlistsAdapter.get_startlist_by_id(db, id)
        # update the startlist if found:
        if old_startlist:
            if startlist.id != old_startlist["id"]:
                raise IllegalValueException("Cannot change id for startlist.")
            new_startlist = startlist.to_dict()
            result = await StartlistsAdapter.update_startlist(db, id, new_startlist)
            return result
        raise StartlistNotFoundException(f"Startlist with id {id} not found.")

    @classmethod
    async def delete_startlist(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get startlist function."""
        # get old document
        startlist = await StartlistsAdapter.get_startlist_by_id(db, id)
        # delete the document if found:
        if startlist:
            result = await StartlistsAdapter.delete_startlist(db, id)
            return result
        raise StartlistNotFoundException(f"Startlist with id {id} not found")


#   Validation:
async def validate_startlist(db: Any, startlist: Startlist) -> None:
    """Validate the startlist."""
    # Validate start_events:
    # TODO: validate race-properties.
    if startlist.start_events:
        for _start_event in startlist.start_events:
            pass
