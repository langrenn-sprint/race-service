"""Module for race_result adapter."""

from typing import Any
from uuid import UUID

from app.models import RaceResult


class RaceResultNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceResultsAdapter:
    """Class representing an adapter for race_results."""

    database: Any

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database

    @classmethod
    async def get_all_race_results(cls: Any) -> list[RaceResult]:  # pragma: no cover
        """Get all race_results function."""
        cursor = cls.database.race_results_collection.find()
        return [
            RaceResult.model_validate(race_result)
            for race_result in await cursor.to_list(None)
        ]

    @classmethod
    async def get_race_results_by_race_id(
        cls: Any, race_id: UUID
    ) -> list[RaceResult]:  # pragma: no cover
        """Get race_result by race_id function."""
        cursor = cls.database.race_results_collection.find({"race_id": race_id})
        return [
            RaceResult.model_validate(race_result)
            for race_result in await cursor.to_list(None)
        ]

    @classmethod
    async def get_race_results_by_race_id_and_timing_point(
        cls: Any, race_id: UUID, timing_point: str
    ) -> list[RaceResult]:  # pragma: no cover
        """Get race_result by race_id function."""
        cursor = cls.database.race_results_collection.find(
            {"$and": [{"race_id": race_id}, {"timing_point": timing_point}]}
        )
        return [
            RaceResult.model_validate(race_result)
            for race_result in await cursor.to_list(None)
        ]

    @classmethod
    async def create_race_result(
        cls: Any, race_result: RaceResult
    ) -> str:  # pragma: no cover
        """Create race_result function."""
        return await cls.database.race_results_collection.insert_one(
            race_result.model_dump()
        )

    @classmethod
    async def get_race_result_by_id(
        cls: Any, id_: UUID
    ) -> RaceResult:  # pragma: no cover
        """Get race_result function."""
        race_result = await cls.database.race_results_collection.find_one({"id": id_})
        if race_result is None:
            msg = f"RaceResult with id {id_} not found"
            raise RaceResultNotFoundError(msg)
        return RaceResult.model_validate(race_result)

    @classmethod
    async def update_race_result(
        cls: Any, id_: UUID, race_result: RaceResult
    ) -> str | None:  # pragma: no cover
        """Get race_result function."""
        return await cls.database.race_results_collection.replace_one(
            {"id": id_}, race_result.model_dump()
        )

    @classmethod
    async def delete_race_result(cls: Any, id_: UUID) -> str | None:  # pragma: no cover
        """Get race_result function."""
        return await cls.database.race_results_collection.delete_one({"id": id_})
