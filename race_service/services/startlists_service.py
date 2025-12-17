"""Module for startlists service."""

import logging
import uuid
from typing import Any

from race_service.adapters import StartlistNotFoundError, StartlistsAdapter
from race_service.models import Startlist

from .exceptions import IllegalValueError


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class CouldNotCreateStartlistError(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartlistAllreadyExistError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartlistsService:
    """Class representing a service for startlists."""

    logger = logging.getLogger(
        "race_service.services.startlists_service.StartlistsService"
    )

    @classmethod
    async def create_startlist(cls: Any, db: Any, startlist: Startlist) -> str:
        """Create startlist function.

        Args:
            db (Any): the db
            startlist (Startlist): a startlist instanse to be created

        Returns:
            str: The id of the created startlist

        Raises:
            IllegalValueError: input object has illegal values
            StartlistAllreadyExistError: event can have zero or one plan
            CouldNotCreateStartlistError: creation failed
        """
        cls.logger.debug(f"trying to insert startlist: {startlist}")
        # Event can have one, and only, one startlist:
        existing_sl = await StartlistsAdapter.get_startlists_by_event_id(
            db, startlist.event_id
        )
        if existing_sl and len(existing_sl) > 0:
            msg = f'Event "{startlist.event_id!r}" already has a startlist.'
            raise StartlistAllreadyExistError(msg)
        # Validation:
        await validate_startlist(startlist)
        if startlist.id:
            msg = "Cannot create startlist with input id."
            raise IllegalValueError(msg)
        # create ids:
        id_ = create_id()
        startlist.id = id_
        # insert new startlist
        cls.logger.debug(f"new startlist: {startlist}")
        result = await StartlistsAdapter.create_startlist(db, startlist)
        cls.logger.debug(f"inserted startlist with id: {id_}")
        if result:
            return id_
        msg = "Creation of startlist failed."
        raise CouldNotCreateStartlistError(msg) from None

    @classmethod
    async def update_startlist(
        cls: Any, db: Any, id_: str, startlist: Startlist
    ) -> str | None:
        """Get startlist function."""
        # get old document
        try:
            old_startlist = await StartlistsAdapter.get_startlist_by_id(db, id_)
        except StartlistNotFoundError as e:
            raise e from e
        # update the startlist if found:
        if startlist.id != old_startlist.id:
            msg = "Cannot change id for startlist."
            raise IllegalValueError(msg)
        return await StartlistsAdapter.update_startlist(db, id_, startlist)

    @classmethod
    async def delete_startlist(cls: Any, db: Any, id_: str) -> str | None:
        """Get startlist function."""
        # get old document
        try:
            await StartlistsAdapter.get_startlist_by_id(db, id_)
        except StartlistNotFoundError as e:
            raise e from e
        # delete the document if found:
        return await StartlistsAdapter.delete_startlist(db, id_)


#   Validation:
async def validate_startlist(startlist: Startlist) -> None:
    """Validate the startlist."""
    if startlist.start_entries:
        for _start_entry in startlist.start_entries:
            pass
