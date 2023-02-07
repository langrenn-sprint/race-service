"""Module for start_entries service."""
import logging
from typing import Any, Optional
import uuid

from race_service.adapters import StartEntriesAdapter, StartEntryNotFoundException
from race_service.models import StartEntry
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class CouldNotCreateStartEntryException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartEntriesService:
    """Class representing a service for start_entries."""

    @classmethod
    async def create_start_entry(cls: Any, db: Any, start_entry: StartEntry) -> str:
        """Create start_entry function.

        Args:
            db (Any): the db
            start_entry (StartEntry): a start_entry instanse to be created

        Returns:
            str: The id of the created start_entry

        Raises:
            IllegalValueException: input object has illegal values
            CouldNotCreateStartEntryException: creation failed
        """
        logging.debug(f"trying to insert start_entry: {start_entry}")
        # Validation:
        await validate_start_entry(db, start_entry)
        if start_entry.id:
            raise IllegalValueException("Cannot create start_entry with input id.")
        # create ids:
        id = create_id()
        start_entry.id = id
        # insert new start_entry
        logging.debug(f"new start_entry: {start_entry}")
        result = await StartEntriesAdapter.create_start_entry(db, start_entry)
        logging.debug(f"inserted start_entry with id: {id}")
        if result:
            return id
        raise CouldNotCreateStartEntryException(
            "Creation of start-entry failed."
        ) from None

    @classmethod
    async def update_start_entry(
        cls: Any, db: Any, id: str, start_entry: StartEntry
    ) -> Optional[str]:
        """Update start_entry function."""
        # get old document
        try:
            old_start_entry = await StartEntriesAdapter.get_start_entry_by_id(db, id)
        except StartEntryNotFoundException as e:
            raise e
        # update the start_entry if found:
        if start_entry.id != old_start_entry.id:
            raise IllegalValueException("Cannot change id for start_entry.")
        result = await StartEntriesAdapter.update_start_entry(db, id, start_entry)
        return result

    @classmethod
    async def delete_start_entry(cls: Any, db: Any, id: str) -> Optional[str]:
        """Delete start_entry function."""
        # get old document
        try:
            await StartEntriesAdapter.get_start_entry_by_id(db, id)
        except StartEntryNotFoundException as e:
            raise e
        # delete the document if found:
        result = await StartEntriesAdapter.delete_start_entry(db, id)
        return result


#   Validation:
async def validate_start_entry(db: Any, start_entry: StartEntry) -> None:
    """Validate the start_entry."""
    # Validate start_entries:
    # TODO: validate start_entry-properties.
    pass
