"""Module for timeevent adapter."""
import logging
from typing import Any, List, Optional


class TimeeventsAdapter:
    """Class representing an adapter for timeevents."""

    @classmethod
    async def get_all_timeevents(cls: Any, db: Any) -> List:  # pragma: no cover
        """Get all timeevents function."""
        timeevents: List = []
        cursor = db.timeevents_collection.find()
        for timeevent in await cursor.to_list(length=100):
            timeevents.append(timeevent)
            logging.debug(timeevent)
        return timeevents

    @classmethod
    async def create_timeevent(
        cls: Any, db: Any, timeevent: dict
    ) -> str:  # pragma: no cover
        """Create timeevent function."""
        result = await db.timeevents_collection.insert_one(timeevent)
        return result

    @classmethod
    async def get_timeevent_by_id(
        cls: Any, db: Any, id: str
    ) -> dict:  # pragma: no cover
        """Get timeevent function."""
        result = await db.timeevents_collection.find_one({"id": id})
        return result

    @classmethod
    async def get_timeevents_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List:  # pragma: no cover
        """Get timeevents by event_id function."""
        timeevents: List = []
        cursor = db.timeevents_collection.find({"event_id": event_id})
        for timeevent in await cursor.to_list(length=100):
            timeevents.append(timeevent)
        return timeevents

    @classmethod
    async def update_timeevent(
        cls: Any, db: Any, id: str, timeevent: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get timeevent function."""
        result = await db.timeevents_collection.replace_one({"id": id}, timeevent)
        return result

    @classmethod
    async def delete_timeevent(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get timeevent function."""
        result = await db.timeevents_collection.delete_one({"id": id})
        return result
