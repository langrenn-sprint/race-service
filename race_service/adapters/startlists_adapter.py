"""Module for startlist adapter."""
from typing import Any, List, Optional


from race_service.models import Startlist


class StartlistNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartlistsAdapter:
    """Class representing an adapter for startlists."""

    @classmethod
    async def get_all_startlists(
        cls: Any, db: Any
    ) -> List[Startlist]:  # pragma: no cover
        """Get all startlists function."""
        startlists: List = []
        cursor = db.startlists_collection.find()
        for startlist in await cursor.to_list(None):
            startlists.append(Startlist.from_dict(startlist))
        return startlists

    @classmethod
    async def create_startlist(
        cls: Any, db: Any, startlist: Startlist
    ) -> str:  # pragma: no cover
        """Create startlist function."""
        result = await db.startlists_collection.insert_one(startlist.to_dict())
        return result

    @classmethod
    async def get_startlist_by_id(
        cls: Any, db: Any, id: str
    ) -> Startlist:  # pragma: no cover
        """Get startlist function."""
        startlist = await db.startlists_collection.find_one({"id": id})
        if startlist is None:
            raise StartlistNotFoundException(f"Startlist with id {id} not found.")
        return Startlist.from_dict(startlist)

    @classmethod
    async def get_startlists_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List[Startlist]:  # pragma: no cover
        """Get startlists by event_id function."""
        startlists: List = []
        cursor = db.startlists_collection.find({"event_id": event_id})
        for startlist in await cursor.to_list(None):
            startlists.append(Startlist.from_dict(startlist))
        return startlists

    @classmethod
    async def update_startlist(
        cls: Any, db: Any, id: str, startlist: Startlist
    ) -> Optional[str]:  # pragma: no cover
        """Get startlist function."""
        result = await db.startlists_collection.replace_one(
            {"id": id}, startlist.to_dict()
        )
        return result

    @classmethod
    async def delete_startlist(
        cls: Any, db: Any, id: str
    ) -> Optional[str]:  # pragma: no cover
        """Get startlist function."""
        result = await db.startlists_collection.delete_one({"id": id})
        return result
