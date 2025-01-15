"""Module for startlist adapter."""

from typing import Any

from race_service.models import Startlist


class StartlistNotFoundError(Exception):
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
    ) -> list[Startlist]:  # pragma: no cover
        """Get all startlists function."""
        cursor = db.startlists_collection.find()
        return [
            Startlist.from_dict(startlist) for startlist in await cursor.to_list(None)
        ]

    @classmethod
    async def create_startlist(
        cls: Any, db: Any, startlist: Startlist
    ) -> str:  # pragma: no cover
        """Create startlist function."""
        return await db.startlists_collection.insert_one(startlist.to_dict())

    @classmethod
    async def get_startlist_by_id(
        cls: Any, db: Any, id_: str
    ) -> Startlist:  # pragma: no cover
        """Get startlist function."""
        startlist = await db.startlists_collection.find_one({"id": id_})
        if startlist is None:
            msg = f"Startlist with id {id_} not found."
            raise StartlistNotFoundError(msg)
        return Startlist.from_dict(startlist)

    @classmethod
    async def get_startlists_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> list[Startlist]:  # pragma: no cover
        """Get startlists by event_id function."""
        cursor = db.startlists_collection.find({"event_id": event_id})
        return [
            Startlist.from_dict(startlist) for startlist in await cursor.to_list(None)
        ]

    @classmethod
    async def update_startlist(
        cls: Any, db: Any, id_: str, startlist: Startlist
    ) -> str | None:  # pragma: no cover
        """Get startlist function."""
        return await db.startlists_collection.replace_one(
            {"id": id_}, startlist.to_dict()
        )

    @classmethod
    async def delete_startlist(
        cls: Any, db: Any, id_: str
    ) -> str | None:  # pragma: no cover
        """Get startlist function."""
        return await db.startlists_collection.delete_one({"id": id_})
