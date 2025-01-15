"""Module for race_result adapter."""

from typing import Any

from race_service.models import RaceResult


class RaceResultNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceResultsAdapter:
    """Class representing an adapter for race_results."""

    @classmethod
    async def get_all_race_results(
        cls: Any, db: Any
    ) -> list[RaceResult]:  # pragma: no cover
        """Get all race_results function."""
        cursor = db.race_results_collection.find()
        return [
            RaceResult.from_dict(race_result)
            for race_result in await cursor.to_list(None)
        ]

    @classmethod
    async def get_race_results_by_race_id(
        cls: Any, db: Any, race_id: str
    ) -> list[RaceResult]:  # pragma: no cover
        """Get race_result by race_id function."""
        cursor = db.race_results_collection.find({"race_id": race_id})
        return [
            RaceResult.from_dict(race_result)
            for race_result in await cursor.to_list(None)
        ]

    @classmethod
    async def get_race_results_by_race_id_and_timing_point(
        cls: Any, db: Any, race_id: str, timing_point: str
    ) -> list[RaceResult]:  # pragma: no cover
        """Get race_result by race_id function."""
        cursor = db.race_results_collection.find(
            {"$and": [{"race_id": race_id}, {"timing_point": timing_point}]}
        )
        return [
            RaceResult.from_dict(race_result)
            for race_result in await cursor.to_list(None)
        ]

    @classmethod
    async def create_race_result(
        cls: Any, db: Any, race_result: RaceResult
    ) -> str:  # pragma: no cover
        """Create race_result function."""
        return await db.race_results_collection.insert_one(race_result.to_dict())

    @classmethod
    async def get_race_result_by_id(
        cls: Any, db: Any, id_: str
    ) -> RaceResult:  # pragma: no cover
        """Get race_result function."""
        race_result = await db.race_results_collection.find_one({"id": id_})
        if race_result is None:
            msg = f"RaceResult with id {id_} not found"
            raise RaceResultNotFoundError(msg)
        return RaceResult.from_dict(race_result)

    @classmethod
    async def update_race_result(
        cls: Any, db: Any, id_: str, race_result: RaceResult
    ) -> str | None:  # pragma: no cover
        """Get race_result function."""
        return await db.race_results_collection.replace_one(
            {"id": id_}, race_result.to_dict()
        )

    @classmethod
    async def delete_race_result(
        cls: Any, db: Any, id_: str
    ) -> str | None:  # pragma: no cover
        """Get race_result function."""
        return await db.race_results_collection.delete_one({"id": id_})
