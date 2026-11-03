"""Module for raceplan adapter."""

import logging
from typing import Any
from uuid import UUID

from app.models import Raceplan


class RaceplanNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceplansAdapter:
    """Class representing an adapter for raceplans."""

    database: Any
    logger: logging.Logger

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database
        cls.logger = logging.getLogger("uvicorn.error")

    @classmethod
    async def get_all_raceplans(cls: Any) -> list[Raceplan]:  # pragma: no cover
        """Get all raceplans function."""
        cursor = cls.database.raceplans_collection.find()
        return [
            Raceplan.model_validate(raceplan) for raceplan in await cursor.to_list(None)
        ]

    @classmethod
    async def create_raceplan(cls: Any, raceplan: Raceplan) -> str:  # pragma: no cover
        """Create raceplan function."""
        return await cls.database.raceplans_collection.insert_one(raceplan.model_dump())

    @classmethod
    async def get_raceplan_by_id(cls: Any, id_: UUID) -> Raceplan:  # pragma: no cover
        """Get raceplan function."""
        result = await cls.database.raceplans_collection.find_one({"id": id_})
        if not result:
            msg = f"Raceplan with id {id_} not found."
            raise RaceplanNotFoundError(msg)
        return Raceplan.model_validate(result)

    @classmethod
    async def get_raceplans_by_event_id(
        cls: Any, event_id: UUID
    ) -> list[Raceplan]:  # pragma: no cover
        """Get raceplan by event_id function."""
        raceplans: list[Raceplan] = []
        result = await cls.database.raceplans_collection.find_one(
            {"event_id": event_id}
        )
        if result:
            raceplans.append(Raceplan.model_validate(result))
        return raceplans

    @classmethod
    async def update_raceplan(
        cls: Any, id_: UUID, raceplan: Raceplan
    ) -> str | None:  # pragma: no cover
        """Get raceplan function."""
        return await cls.database.raceplans_collection.replace_one(
            {"id": id_}, raceplan.model_dump()
        )

    @classmethod
    async def delete_raceplan(cls: Any, id_: UUID) -> str | None:  # pragma: no cover
        """Get raceplan function."""
        return await cls.database.raceplans_collection.delete_one({"id": id_})
