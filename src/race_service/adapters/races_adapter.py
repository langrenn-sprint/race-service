"""Module for race adapter."""
import logging
from typing import Any, List, Optional


class RacesAdapter:
    """Class representing an adapter for races."""

    @classmethod
    async def get_all_races(cls: Any, db: Any) -> List[dict]:  # pragma: no cover
        """Get all races function."""
        races: List = []
        cursor = db.races_collection.find()
        for race in await cursor.to_list(None):
            races.append(race)
            logging.debug(race)
        return races

    @classmethod
    async def create_race(cls: Any, db: Any, race: dict) -> str:  # pragma: no cover
        """Create race function."""
        result = await db.races_collection.insert_one(race)
        return result

    @classmethod
    async def get_race_by_id(cls: Any, db: Any, id: str) -> dict:  # pragma: no cover
        """Get race function."""
        result = await db.races_collection.find_one({"id": id})
        return result

    @classmethod
    async def get_races_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List[dict]:  # pragma: no cover
        """Get races by event_id function."""
        races: List = []
        cursor = db.races_collection.find({"event_id": event_id})
        for race in await cursor.to_list(None):
            races.append(race)
            logging.debug(race)
        return races

    @classmethod
    async def get_races_by_raceplan_id(
        cls: Any, db: Any, raceplan_id: str
    ) -> List[dict]:  # pragma: no cover
        """Get races by raceplan_id function."""
        races: List = []
        cursor = db.races_collection.find({"raceplan_id": raceplan_id})
        for race in await cursor.to_list(None):
            races.append(race)
            logging.debug(race)
        return races

    @classmethod
    async def update_race(
        cls: Any, db: Any, id: str, race: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get race function."""
        result = await db.races_collection.replace_one({"id": id}, race)
        return result

    @classmethod
    async def delete_race(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get race function."""
        result = await db.races_collection.delete_one({"id": id})
        return result
