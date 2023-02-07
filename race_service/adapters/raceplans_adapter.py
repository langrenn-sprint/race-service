"""Module for raceplan adapter."""
from typing import Any, List, Optional

from race_service.models import Raceplan


class RaceplanNotFoundException(Exception):
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
    ) -> List[Raceplan]:  # pragma: no cover
        """Get all raceplans function."""
        raceplans: List[Raceplan] = []
        cursor = db.raceplans_collection.find()
        for raceplan in await cursor.to_list(None):
            raceplans.append(Raceplan.from_dict(raceplan))
        return raceplans

    @classmethod
    async def create_raceplan(
        cls: Any, db: Any, raceplan: Raceplan
    ) -> str:  # pragma: no cover
        """Create raceplan function."""
        result = await db.raceplans_collection.insert_one(raceplan.to_dict())
        return result

    @classmethod
    async def get_raceplan_by_id(
        cls: Any, db: Any, id: str
    ) -> Raceplan:  # pragma: no cover
        """Get raceplan function."""
        result = await db.raceplans_collection.find_one({"id": id})
        if not result:
            raise RaceplanNotFoundException(f"Raceplan with id {id} not found.")
        return Raceplan.from_dict(result)

    @classmethod
    async def get_raceplans_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List[Raceplan]:  # pragma: no cover
        """Get raceplan by event_id function."""
        raceplans: List[Raceplan] = []
        result = await db.raceplans_collection.find_one({"event_id": event_id})
        if result:
            raceplans.append(Raceplan.from_dict(result))
        return raceplans

    @classmethod
    async def update_raceplan(
        cls: Any, db: Any, id: str, raceplan: Raceplan
    ) -> Optional[str]:  # pragma: no cover
        """Get raceplan function."""
        result = await db.raceplans_collection.replace_one(
            {"id": id}, raceplan.to_dict()
        )
        return result

    @classmethod
    async def delete_raceplan(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get raceplan function."""
        result = await db.raceplans_collection.delete_one({"id": id})
        return result
