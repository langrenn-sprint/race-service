"""Module for time_event adapter."""
from typing import Any, List, Optional


class TimeEventsAdapter:
    """Class representing an adapter for time_events."""

    @classmethod
    async def get_all_time_events(cls: Any, db: Any) -> List:  # pragma: no cover
        """Get all time_events function."""
        time_events: List = []
        cursor = db.time_events_collection.find()
        for time_event in await cursor.to_list(None):
            time_events.append(time_event)
        return time_events

    @classmethod
    async def create_time_event(
        cls: Any, db: Any, time_event: dict
    ) -> str:  # pragma: no cover
        """Create time_event function."""
        result = await db.time_events_collection.insert_one(time_event)
        return result

    @classmethod
    async def get_time_event_by_id(
        cls: Any, db: Any, id: str
    ) -> dict:  # pragma: no cover
        """Get time_event function."""
        result = await db.time_events_collection.find_one({"id": id})
        return result

    @classmethod
    async def get_time_events_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List:  # pragma: no cover
        """Get time_events by event_id function."""
        time_events: List = []
        cursor = db.time_events_collection.find({"event_id": event_id})
        for time_event in await cursor.to_list(None):
            time_events.append(time_event)
        return time_events

    @classmethod
    async def get_time_events_by_event_id_and_timing_point(
        cls: Any, db: Any, event_id: str, timing_point: str
    ) -> List:  # pragma: no cover
        """Get time_events by event_id function."""
        time_events: List = []
        cursor = db.time_events_collection.find(
            {"$and": [{"event_id": event_id, "timing_point": timing_point}]}
        )
        for time_event in await cursor.to_list(None):
            time_events.append(time_event)
        return time_events

    @classmethod
    async def get_time_events_by_race_id(
        cls: Any, db: Any, race_id: str
    ) -> List:  # pragma: no cover
        """Get time_events by race_id function."""
        time_events: List = []
        cursor = db.time_events_collection.find({"race_id": race_id})
        for time_event in await cursor.to_list(None):
            time_events.append(time_event)
        return time_events

    @classmethod
    async def update_time_event(
        cls: Any, db: Any, id: str, time_event: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get time_event function."""
        result = await db.time_events_collection.replace_one({"id": id}, time_event)
        return result

    @classmethod
    async def delete_time_event(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get time_event function."""
        result = await db.time_events_collection.delete_one({"id": id})
        return result
