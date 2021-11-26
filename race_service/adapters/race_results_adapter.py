"""Module for race_result adapter."""
from typing import Any, List, Optional


class RaceResultsAdapter:
    """Class representing an adapter for race_results."""

    @classmethod
    async def get_all_race_results(cls: Any, db: Any) -> List:  # pragma: no cover
        """Get all race_results function."""
        race_results: List = []
        cursor = db.race_results_collection.find()
        for race_result in await cursor.to_list(None):
            race_results.append(race_result)
        return race_results

    @classmethod
    async def get_race_results_by_race_id(
        cls: Any, db: Any, race_id: str
    ) -> List[dict]:  # pragma: no cover
        """Get race_result by race_id function."""
        race_results: List = []
        cursor = db.race_results_collection.find({"race_id": race_id})
        for race_result in await cursor.to_list(None):
            race_results.append(race_result)
        return race_results

    @classmethod
    async def get_race_results_by_race_id_and_timing_point(
        cls: Any, db: Any, race_id: str, timing_point: str
    ) -> List[dict]:  # pragma: no cover
        """Get race_result by race_id function."""
        race_results: List = []
        cursor = db.race_results_collection.find(
            {"$and": [{"race_id": race_id}, {"timing_point": timing_point}]}
        )
        for race_result in await cursor.to_list(None):
            race_results.append(race_result)
        return race_results

    @classmethod
    async def create_race_result(
        cls: Any, db: Any, race_result: dict
    ) -> str:  # pragma: no cover
        """Create race_result function."""
        result = await db.race_results_collection.insert_one(race_result)
        return result

    @classmethod
    async def get_race_result_by_id(
        cls: Any, db: Any, id: str
    ) -> dict:  # pragma: no cover
        """Get race_result function."""
        result = await db.race_results_collection.find_one({"id": id})
        return result

    @classmethod
    async def update_race_result(
        cls: Any, db: Any, id: str, race_result: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get race_result function."""
        result = await db.race_results_collection.replace_one({"id": id}, race_result)
        return result

    @classmethod
    async def delete_race_result(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get race_result function."""
        result = await db.race_results_collection.delete_one({"id": id})
        return result
