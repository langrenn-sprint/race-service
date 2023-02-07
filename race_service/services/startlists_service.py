"""Module for startlists service."""
import logging
from typing import Any, Optional
import uuid

from race_service.adapters import StartlistNotFoundException, StartlistsAdapter
from race_service.models import Startlist
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class CouldNotCreateStartlistException(Exception):
    """Class representing custom exception for command."""

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
    async def create_startlist(cls: Any, db: Any, startlist: Startlist) -> str:
        """Create startlist function.

        Args:
            db (Any): the db
            startlist (Startlist): a startlist instanse to be created

        Returns:
            str: The id of the created startlist

        Raises:
            IllegalValueException: input object has illegal values
            StartlistAllreadyExistException: event can have zero or one plan
            CouldNotCreateStartlistException: creation failed
        """
        logging.debug(f"trying to insert startlist: {startlist}")
        # Event can have one, and only, one startlist:
        existing_sl = await StartlistsAdapter.get_startlists_by_event_id(
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
        # insert new startlist
        logging.debug(f"new startlist: {startlist}")
        result = await StartlistsAdapter.create_startlist(db, startlist)
        logging.debug(f"inserted startlist with id: {id}")
        if result:
            return id
        raise CouldNotCreateStartlistException(
            "Creation of startlist failed."
        ) from None

    @classmethod
    async def update_startlist(
        cls: Any, db: Any, id: str, startlist: Startlist
    ) -> Optional[str]:
        """Get startlist function."""
        # get old document
        try:
            old_startlist = await StartlistsAdapter.get_startlist_by_id(db, id)
        except StartlistNotFoundException as e:
            raise e
        # update the startlist if found:
        if startlist.id != old_startlist.id:
            raise IllegalValueException("Cannot change id for startlist.")
        result = await StartlistsAdapter.update_startlist(db, id, startlist)
        return result

    @classmethod
    async def delete_startlist(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get startlist function."""
        # get old document
        try:
            await StartlistsAdapter.get_startlist_by_id(db, id)
        except StartlistNotFoundException as e:
            raise e
        # delete the document if found:
        result = await StartlistsAdapter.delete_startlist(db, id)
        return result


#   Validation:
async def validate_startlist(db: Any, startlist: Startlist) -> None:
    """Validate the startlist."""
    # TODO: Validate startlist-properties:
    if startlist.start_entries:
        for _start_entry in startlist.start_entries:
            pass
