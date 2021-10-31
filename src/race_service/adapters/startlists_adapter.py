"""Module for startlist adapter."""
import logging
from typing import Any, List, Optional


class StartlistsAdapter:
    """Class representing an adapter for startlists."""

    @classmethod
    async def get_all_startlists(cls: Any, db: Any) -> List:  # pragma: no cover
        """Get all startlists function."""
        startlists: List = []
        cursor = db.startlists_collection.find()
        for startlist in await cursor.to_list(None):
            startlists.append(startlist)
            logging.debug(startlist)
        return startlists

    @classmethod
    async def create_startlist(
        cls: Any, db: Any, startlist: dict
    ) -> str:  # pragma: no cover
        """Create startlist function."""
        result = await db.startlists_collection.insert_one(startlist)
        return result

    @classmethod
    async def get_startlist_by_id(
        cls: Any, db: Any, id: str
    ) -> dict:  # pragma: no cover
        """Get startlist function."""
        result = await db.startlists_collection.find_one({"id": id})
        return result

    @classmethod
    async def get_startlist_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List[dict]:  # pragma: no cover
        """Get startlist by event_id function."""
        startlists: List = []
        result = await db.startlists_collection.find_one({"event_id": event_id})
        if result:
            startlists.append(result)
        return startlists

    @classmethod
    async def update_startlist(
        cls: Any, db: Any, id: str, startlist: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get startlist function."""
        result = await db.startlists_collection.replace_one({"id": id}, startlist)
        return result

    @classmethod
    async def delete_startlist(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get startlist function."""
        result = await db.startlists_collection.delete_one({"id": id})
        return result
