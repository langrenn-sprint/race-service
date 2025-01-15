"""Module for raceplan adapter."""

from typing import Any

from race_service.models import Raceplan


class RaceplanNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceplansAdapter:
    """Class representing an adapter for raceplans."""

    @classmethod
    async def get_all_raceplans(
        cls: Any, db: Any
    ) -> list[Raceplan]:  # pragma: no cover
        """Get all raceplans function."""
        cursor = db.raceplans_collection.find()
        return [Raceplan.from_dict(raceplan) for raceplan in await cursor.to_list(None)]

    @classmethod
    async def create_raceplan(
        cls: Any, db: Any, raceplan: Raceplan
    ) -> str:  # pragma: no cover
        """Create raceplan function."""
        return await db.raceplans_collection.insert_one(raceplan.to_dict())

    @classmethod
    async def get_raceplan_by_id(
        cls: Any, db: Any, id_: str
    ) -> Raceplan:  # pragma: no cover
        """Get raceplan function."""
        result = await db.raceplans_collection.find_one({"id": id_})
        if not result:
            msg = f"Raceplan with id {id_} not found."
            raise RaceplanNotFoundError(msg)
        return Raceplan.from_dict(result)

    @classmethod
    async def get_raceplans_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> list[Raceplan]:  # pragma: no cover
        """Get raceplan by event_id function."""
        raceplans: list[Raceplan] = []
        result = await db.raceplans_collection.find_one({"event_id": event_id})
        if result:
            raceplans.append(Raceplan.from_dict(result))
        return raceplans

    @classmethod
    async def update_raceplan(
        cls: Any, db: Any, id_: str, raceplan: Raceplan
    ) -> str | None:  # pragma: no cover
        """Get raceplan function."""
        return await db.raceplans_collection.replace_one(
            {"id": id_}, raceplan.to_dict()
        )

    @classmethod
    async def delete_raceplan(
        cls: Any, db: Any, id_: str
    ) -> str | None:  # pragma: no cover
        """Get raceplan function."""
        return await db.raceplans_collection.delete_one({"id": id_})
