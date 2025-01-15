"""Module for start_entry adapter."""

from typing import Any

from race_service.models import StartEntry


class StartEntryNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartEntriesAdapter:
    """Class representing an adapter for start_entries."""

    @classmethod
    async def get_start_entries_by_race_id(
        cls: Any, db: Any, race_id: str
    ) -> list[StartEntry]:  # pragma: no cover
        """Get start_entries by race_id function."""
        cursor = db.start_entries_collection.find({"race_id": race_id}).sort(
            [("starting_position", 1)]
        )
        return [
            StartEntry.from_dict(start_entry)
            for start_entry in await cursor.to_list(None)
        ]

    @classmethod
    async def get_start_entries_by_race_id_and_startlist_id(
        cls: Any, db: Any, race_id: str, startlist_id: str
    ) -> list[StartEntry]:  # pragma: no cover
        """Get start_entries by race_id and startlist_id function."""
        cursor = db.start_entries_collection.find(
            {
                "$and": [
                    {"race_id": race_id},
                    {"startlist_id": startlist_id},
                ]
            }
        ).sort([("starting_position", 1)])
        return [
            StartEntry.from_dict(start_entry)
            for start_entry in await cursor.to_list(None)
        ]

    @classmethod
    async def create_start_entry(
        cls: Any, db: Any, start_entry: StartEntry
    ) -> str:  # pragma: no cover
        """Create start_entry function."""
        return await db.start_entries_collection.insert_one(start_entry.to_dict())

    @classmethod
    async def get_start_entry_by_id(
        cls: Any, db: Any, id_: str
    ) -> StartEntry:  # pragma: no cover
        """Get start_entry function."""
        start_entry = await db.start_entries_collection.find_one({"id": id_})
        if not start_entry:
            msg = f"StartEntry with id {id_} not found"
            raise StartEntryNotFoundError(msg)
        return StartEntry.from_dict(start_entry)

    @classmethod
    async def update_start_entry(
        cls: Any, db: Any, id_: str, start_entry: StartEntry
    ) -> str | None:  # pragma: no cover
        """Get start_entry function."""
        return await db.start_entries_collection.replace_one(
            {"id": id_}, start_entry.to_dict()
        )

    @classmethod
    async def delete_start_entry(
        cls: Any, db: Any, id_: str
    ) -> str | None:  # pragma: no cover
        """Get start_entry function."""
        return await db.start_entries_collection.delete_one({"id": id_})
