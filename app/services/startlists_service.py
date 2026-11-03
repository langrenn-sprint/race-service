"""Module for startlists service."""

import logging
from typing import Any
from uuid import UUID

from app.adapters import StartlistNotFoundError, StartlistsAdapter
from app.models import Startlist

from .exceptions import IllegalValueError


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
    async def create_startlist(cls: Any, startlist: Startlist) -> UUID:
        """Create startlist function.

        Args:
            startlist (Startlist): a startlist instanse to be created

        Returns:
            UUID: The id of the created startlist

        Raises:
            StartlistAllreadyExistError: event can have zero or one plan
            CouldNotCreateStartlistError: creation failed
        """
        cls.logger.debug(f"trying to insert startlist: {startlist}")
        # Event can have one, and only, one startlist:
        existing_sl = await StartlistsAdapter.get_startlists_by_event_id(
            startlist.event_id
        )
        if existing_sl and len(existing_sl) > 0:
            msg = f'Event "{startlist.event_id}" already has a startlist.'
            raise StartlistAllreadyExistError(msg)
        # Validation:
        await validate_startlist(startlist)
        # insert new startlist
        cls.logger.debug(f"new startlist: {startlist}")
        result = await StartlistsAdapter.create_startlist(startlist)
        cls.logger.debug(f"inserted startlist with id: {startlist.id}")
        if result:
            return startlist.id
        msg = "Creation of startlist failed."
        raise CouldNotCreateStartlistError(msg) from None

    @classmethod
    async def update_startlist(cls: Any, id_: UUID, startlist: Startlist) -> str | None:
        """Get startlist function."""
        # get old document
        try:
            old_startlist = await StartlistsAdapter.get_startlist_by_id(id_)
        except StartlistNotFoundError as e:
            raise e from e
        # update the startlist if found:
        if startlist.id != old_startlist.id:
            msg = "Cannot change id for startlist."
            raise IllegalValueError(msg)
        return await StartlistsAdapter.update_startlist(id_, startlist)

    @classmethod
    async def delete_startlist(cls: Any, id_: UUID) -> str | None:
        """Get startlist function."""
        # get old document
        try:
            await StartlistsAdapter.get_startlist_by_id(id_)
        except StartlistNotFoundError as e:
            raise e from e
        # delete the document if found:
        return await StartlistsAdapter.delete_startlist(id_)


#   Validation:
async def validate_startlist(startlist: Startlist) -> None:
    """Validate the startlist."""
    if startlist.start_entries:
        for _start_entry in startlist.start_entries:
            pass
