"""Module for raceplan adapter."""
import logging
from typing import Any, List, Optional


class RaceplansAdapter:
    """Class representing an adapter for raceplans."""

    @classmethod
    async def get_all_raceplans(cls: Any, db: Any) -> List:  # pragma: no cover
        """Get all raceplans function."""
        raceplans: List = []
        cursor = db.raceplans_collection.find()
        for raceplan in await cursor.to_list(length=100):
            raceplans.append(raceplan)
            logging.debug(raceplan)
        return raceplans

    @classmethod
    async def create_raceplan(
        cls: Any, db: Any, raceplan: dict
    ) -> str:  # pragma: no cover
        """Create raceplan function."""
        result = await db.raceplans_collection.insert_one(raceplan)
        return result

    @classmethod
    async def get_raceplan_by_id(
        cls: Any, db: Any, id: str
    ) -> dict:  # pragma: no cover
        """Get raceplan function."""
        result = await db.raceplans_collection.find_one({"id": id})
        return result

    @classmethod
    async def get_raceplan_by_name(
        cls: Any, db: Any, raceplanname: str
    ) -> dict:  # pragma: no cover
        """Get raceplan function."""
        result = await db.raceplans_collection.find_one({"raceplanname": raceplanname})
        return result

    @classmethod
    async def update_raceplan(
        cls: Any, db: Any, id: str, raceplan: dict
    ) -> Optional[str]:  # pragma: no cover
        """Get raceplan function."""
        result = await db.raceplans_collection.replace_one({"id": id}, raceplan)
        return result

    @classmethod
    async def delete_raceplan(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get raceplan function."""
        result = await db.raceplans_collection.delete_one({"id": id})
        return result
