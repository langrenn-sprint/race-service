"""Module for start_entry adapter."""
from typing import Any, List, Optional


class StartEntriesAdapter:
    """Class representing an adapter for start_entries."""

    @classmethod
    async def get_all_start_entries(
        cls: Any, db: Any
    ) -> List[dict]:  # pragma: no cover
        """Get all start_entries function."""
        start_entries: List = []
        cursor = db.start_entries_collection.find()
        for start_entry in await cursor.to_list(None):
            start_entries.append(start_entry)
        return start_entries

    @classmethod
    async def create_start_entry(
        cls: Any, db: Any, start_entry: dict
    ) -> str:  # pragma: no cover
        """Create start_entry function."""
        result = await db.start_entries_collection.insert_one(start_entry)
        return result

    @classmethod
    async def get_start_entry_by_id(
        cls: Any, db: Any, id: str
    ) -> dict:  # pragma: no cover
        """Get start_entry function."""
        result = await db.start_entries_collection.find_one({"id": id})
        return result

    @classmethod
    async def get_start_entries_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List[dict]:  # pragma: no cover
        """Get start_entries by event_id function."""
        start_entries: List = []
        cursor = db.start_entries_collection.find({"event_id": event_id})
        for start_entry in await cursor.to_list(None):
            start_entries.append(start_entry)
        return start_entries

    @classmethod
    async def get_start_entries_by_startlist_id(
        cls: Any, db: Any, startlist_id: str
    ) -> List[dict]:  # pragma: no cover
        """Get start_entries by startlist_id function."""
        start_entries: List = []
        cursor = db.start_entries_collection.find({"startlist_id": startlist_id})
        for start_entry in await cursor.to_list(None):
            start_entries.append(start_entry)
        return start_entries

    @classmethod
    async def update_start_entry(
        cls: Any, db: Any, id: str, start_entry: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get start_entry function."""
        result = await db.start_entries_collection.replace_one({"id": id}, start_entry)
        return result

    @classmethod
    async def delete_start_entry(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get start_entry function."""
        result = await db.start_entries_collection.delete_one({"id": id})
        return result
