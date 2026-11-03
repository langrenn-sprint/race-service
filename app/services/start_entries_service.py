"""Module for start_entries service."""

import logging
from typing import Any
from uuid import UUID

from app.adapters import StartEntriesAdapter, StartEntryNotFoundError
from app.models import StartEntry

from .exceptions import IllegalValueError

logger = logging.getLogger(__name__)


class CouldNotCreateStartEntryError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartEntriesService:
    """Class representing a service for start_entries."""

    @classmethod
    async def create_start_entry(cls: Any, start_entry: StartEntry) -> UUID:
        """Create start_entry function.

        Args:
            start_entry (StartEntry): a start_entry instanse to be created

        Returns:
            UUID: The id of the created start_entry

        Raises:
            IllegalValueError: a start_entry with the given id already exists
            CouldNotCreateStartEntryError: creation failed
        """
        logger.debug(f"trying to insert start_entry: {start_entry}")
        # Validation:
        await validate_start_entry(start_entry)
        # The id may be given by the client, so it must not already be in use:
        try:
            await StartEntriesAdapter.get_start_entry_by_id(start_entry.id)
        except StartEntryNotFoundError:
            pass
        else:
            msg = f"Start-entry with id {start_entry.id} already exists."
            raise IllegalValueError(msg) from None
        # insert new start_entry
        logger.debug(f"new start_entry: {start_entry}")
        result = await StartEntriesAdapter.create_start_entry(start_entry)
        logger.debug(f"inserted start_entry with id: {start_entry.id}")
        if result:
            return start_entry.id
        msg = "Creation of start-entry failed."
        raise CouldNotCreateStartEntryError(msg) from None

    @classmethod
    async def update_start_entry(
        cls: Any, id_: UUID, start_entry: StartEntry
    ) -> str | None:
        """Update start_entry function."""
        # get old document
        try:
            old_start_entry = await StartEntriesAdapter.get_start_entry_by_id(id_)
        except StartEntryNotFoundError as e:
            raise e from e
        # update the start_entry if found:
        if start_entry.id != old_start_entry.id:
            msg = "Cannot change id for start_entry."
            raise IllegalValueError(msg)
        return await StartEntriesAdapter.update_start_entry(id_, start_entry)

    @classmethod
    async def delete_start_entry(cls: Any, id_: UUID) -> str | None:
        """Delete start_entry function."""
        # get old document
        try:
            await StartEntriesAdapter.get_start_entry_by_id(id_)
        except StartEntryNotFoundError as e:
            raise e from e
        # delete the document if found:
        return await StartEntriesAdapter.delete_start_entry(id_)


#   Validation:
async def validate_start_entry(start_entry: StartEntry) -> None:
    """Validate the start_entry."""
    # Validate start_entries:
