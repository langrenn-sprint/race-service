"""Module for start_entries service."""

import logging
import uuid
from typing import Any

from race_service.adapters import StartEntriesAdapter, StartEntryNotFoundError
from race_service.models import StartEntry

from .exceptions import IllegalValueError


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class CouldNotCreateStartEntryError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartEntriesService:
    """Class representing a service for start_entries."""

    logger = logging.getLogger("race_service.services.start_entries_service")

    @classmethod
    async def create_start_entry(cls: Any, db: Any, start_entry: StartEntry) -> str:
        """Create start_entry function.

        Args:
            db (Any): the db
            start_entry (StartEntry): a start_entry instanse to be created

        Returns:
            str: The id of the created start_entry

        Raises:
            IllegalValueError: input object has illegal values
            CouldNotCreateStartEntryError: creation failed
        """
        cls.logger.debug(f"trying to insert start_entry: {start_entry}")
        # Validation:
        await validate_start_entry(db, start_entry)
        if start_entry.id:
            msg = "Cannot create start_entry with input id."
            raise IllegalValueError(msg)
        # create ids:
        start_entry_id = create_id()
        start_entry.id = start_entry_id
        # insert new start_entry
        cls.logger.debug(f"new start_entry: {start_entry}")
        result = await StartEntriesAdapter.create_start_entry(db, start_entry)
        cls.logger.debug(f"inserted start_entry with id: {start_entry_id}")
        if result:
            return start_entry_id
        msg = "Creation of start-entry failed."
        raise CouldNotCreateStartEntryError(msg) from None

    @classmethod
    async def update_start_entry(
        cls: Any, db: Any, id_: str, start_entry: StartEntry
    ) -> str | None:
        """Update start_entry function."""
        # get old document
        try:
            old_start_entry = await StartEntriesAdapter.get_start_entry_by_id(db, id_)
        except StartEntryNotFoundError as e:
            raise e from e
        # update the start_entry if found:
        if start_entry.id != old_start_entry.id:
            msg = "Cannot change id for start_entry."
            raise IllegalValueError(msg)
        return await StartEntriesAdapter.update_start_entry(db, id_, start_entry)

    @classmethod
    async def delete_start_entry(cls: Any, db: Any, id_: str) -> str | None:
        """Delete start_entry function."""
        # get old document
        try:
            await StartEntriesAdapter.get_start_entry_by_id(db, id_)
        except StartEntryNotFoundError as e:
            raise e from e
        # delete the document if found:
        return await StartEntriesAdapter.delete_start_entry(db, id_)


#   Validation:
async def validate_start_entry(db: Any, start_entry: StartEntry) -> None:
    """Validate the start_entry."""
    # Validate start_entries:
