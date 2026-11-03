"""Module for startlist adapter."""

from typing import Any
from uuid import UUID

from app.models import Startlist


class StartlistNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class StartlistsAdapter:
    """Class representing an adapter for startlists."""

    database: Any

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database

    @classmethod
    async def get_all_startlists(cls: Any) -> list[Startlist]:  # pragma: no cover
        """Get all startlists function."""
        cursor = cls.database.startlists_collection.find()
        return [
            Startlist.model_validate(startlist)
            for startlist in await cursor.to_list(None)
        ]

    @classmethod
    async def create_startlist(
        cls: Any, startlist: Startlist
    ) -> str:  # pragma: no cover
        """Create startlist function."""
        return await cls.database.startlists_collection.insert_one(
            startlist.model_dump()
        )

    @classmethod
    async def get_startlist_by_id(cls: Any, id_: UUID) -> Startlist:  # pragma: no cover
        """Get startlist function."""
        startlist = await cls.database.startlists_collection.find_one({"id": id_})
        if startlist is None:
            msg = f"Startlist with id {id_} not found."
            raise StartlistNotFoundError(msg)
        return Startlist.model_validate(startlist)

    @classmethod
    async def get_startlists_by_event_id(
        cls: Any, event_id: UUID
    ) -> list[Startlist]:  # pragma: no cover
        """Get startlists by event_id function."""
        cursor = cls.database.startlists_collection.find({"event_id": event_id})
        return [
            Startlist.model_validate(startlist)
            for startlist in await cursor.to_list(None)
        ]

    @classmethod
    async def update_startlist(
        cls: Any, id_: UUID, startlist: Startlist
    ) -> str | None:  # pragma: no cover
        """Get startlist function."""
        return await cls.database.startlists_collection.replace_one(
            {"id": id_}, startlist.model_dump()
        )

    @classmethod
    async def delete_startlist(cls: Any, id_: UUID) -> str | None:  # pragma: no cover
        """Get startlist function."""
        return await cls.database.startlists_collection.delete_one({"id": id_})
