"""Module for time_event adapter."""

import logging
from typing import Any
from uuid import UUID

from app.models import TimeEvent


class TimeEventNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeEventsAdapter:
    """Class representing an adapter for time_events."""

    database: Any
    logger: logging.Logger

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database
        cls.logger = logging.getLogger("uvicorn.error")

    @classmethod
    async def get_all_time_events(cls: Any) -> list[TimeEvent]:  # pragma: no cover
        """Get all time_events function."""
        cursor = cls.database.time_events_collection.find()
        return [
            TimeEvent.model_validate(time_event)
            for time_event in await cursor.to_list(None)
        ]

    @classmethod
    async def create_time_event(
        cls: Any, time_event: TimeEvent
    ) -> str:  # pragma: no cover
        """Create time_event function."""
        return await cls.database.time_events_collection.insert_one(
            time_event.model_dump()
        )

    @classmethod
    async def get_time_event_by_id(
        cls: Any, id_: UUID
    ) -> TimeEvent:  # pragma: no cover
        """Get time_event function."""
        time_event = await cls.database.time_events_collection.find_one({"id": id_})
        if time_event is None:
            msg = f"TimeEvent with id {id_} not found in database."
            raise TimeEventNotFoundError(msg)
        return TimeEvent.model_validate(time_event)

    @classmethod
    async def get_time_events_by_event_id(
        cls: Any, event_id: UUID
    ) -> list[TimeEvent]:  # pragma: no cover
        """Get time_events by event_id function."""
        cursor = cls.database.time_events_collection.find({"event_id": event_id})
        return [
            TimeEvent.model_validate(time_event)
            for time_event in await cursor.to_list(None)
        ]

    @classmethod
    async def get_time_events_by_event_id_and_timing_point(
        cls: Any, event_id: UUID, timing_point: str
    ) -> list[TimeEvent]:  # pragma: no cover
        """Get time_events by event_id function."""
        cursor = cls.database.time_events_collection.find(
            {"$and": [{"event_id": event_id, "timing_point": timing_point}]}
        ).sort([("rank", 1)])
        return [
            TimeEvent.model_validate(time_event)
            for time_event in await cursor.to_list(None)
        ]

    @classmethod
    async def get_time_events_by_event_id_and_bib(
        cls: Any, event_id: UUID, bib: int
    ) -> list[TimeEvent]:  # pragma: no cover
        """Get time_events by event_id function."""
        cursor = cls.database.time_events_collection.find(
            {"$and": [{"event_id": event_id, "bib": bib}]}
        ).sort([("id", 1)])
        return [
            TimeEvent.model_validate(time_event)
            for time_event in await cursor.to_list(None)
        ]

    @classmethod
    async def get_time_events_by_race_id(
        cls: Any, race_id: UUID
    ) -> list[TimeEvent]:  # pragma: no cover
        """Get time_events by race_id function."""
        cursor = cls.database.time_events_collection.find({"race_id": race_id})
        return [
            TimeEvent.model_validate(time_event)
            for time_event in await cursor.to_list(None)
        ]

    @classmethod
    async def update_time_event(
        cls: Any, id_: UUID, time_event: TimeEvent
    ) -> str | None:  # pragma: no cover
        """Get time_event function."""
        return await cls.database.time_events_collection.replace_one(
            {"id": id_}, time_event.model_dump()
        )

    @classmethod
    async def delete_time_event(cls: Any, id_: UUID) -> str | None:  # pragma: no cover
        """Get time_event function."""
        return await cls.database.time_events_collection.delete_one({"id": id_})
