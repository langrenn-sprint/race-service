"""Module for start_entry adapter."""

from typing import Any
from uuid import UUID

from app.models import StartEntry


class StartEntryNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartEntriesAdapter:
    """Class representing an adapter for start_entries."""

    database: Any

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database

    @classmethod
    async def get_start_entries_by_race_id(
        cls: Any, race_id: UUID
    ) -> list[StartEntry]:  # pragma: no cover
        """Get start_entries by race_id function."""
        cursor = cls.database.start_entries_collection.find({"race_id": race_id}).sort(
            [("starting_position", 1)]
        )
        return [
            StartEntry.model_validate(start_entry)
            for start_entry in await cursor.to_list(None)
        ]

    @classmethod
    async def get_start_entries_by_race_id_and_startlist_id(
        cls: Any, race_id: UUID, startlist_id: UUID
    ) -> list[StartEntry]:  # pragma: no cover
        """Get start_entries by race_id and startlist_id function."""
        cursor = cls.database.start_entries_collection.find(
            {
                "$and": [
                    {"race_id": race_id},
                    {"startlist_id": startlist_id},
                ]
            }
        ).sort([("starting_position", 1)])
        return [
            StartEntry.model_validate(start_entry)
            for start_entry in await cursor.to_list(None)
        ]

    @classmethod
    async def create_start_entry(
        cls: Any, start_entry: StartEntry
    ) -> str:  # pragma: no cover
        """Create start_entry function."""
        return await cls.database.start_entries_collection.insert_one(
            start_entry.model_dump()
        )

    @classmethod
    async def get_start_entry_by_id(
        cls: Any, id_: UUID
    ) -> StartEntry:  # pragma: no cover
        """Get start_entry function."""
        start_entry = await cls.database.start_entries_collection.find_one({"id": id_})
        if not start_entry:
            msg = f"StartEntry with id {id_} not found"
            raise StartEntryNotFoundError(msg)
        return StartEntry.model_validate(start_entry)

    @classmethod
    async def update_start_entry(
        cls: Any, id_: UUID, start_entry: StartEntry
    ) -> str | None:  # pragma: no cover
        """Get start_entry function."""
        return await cls.database.start_entries_collection.replace_one(
            {"id": id_}, start_entry.model_dump()
        )

    @classmethod
    async def delete_start_entry(cls: Any, id_: UUID) -> str | None:  # pragma: no cover
        """Get start_entry function."""
        return await cls.database.start_entries_collection.delete_one({"id": id_})
