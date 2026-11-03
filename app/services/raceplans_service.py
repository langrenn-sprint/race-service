"""Module for raceplans service."""

import logging
from typing import Any
from uuid import UUID

from app.adapters import RaceplanNotFoundError, RaceplansAdapter
from app.models import Raceplan

from .exceptions import IllegalValueError


class RaceplanAllreadyExistError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceplansService:
    """Class representing a service for raceplans."""

    logger = logging.getLogger("race_service.raceplans_service.RaceplansService")

    @classmethod
    async def create_raceplan(cls: Any, raceplan: Raceplan) -> UUID | None:
        """Create raceplan function.

        Args:
            raceplan (Raceplan): a raceplan instanse to be created

        Returns:
            Optional[UUID]: The id of the created raceplan. None otherwise.

        Raises:
            RaceplanAllreadyExistError: event can have zero or one plan
        """
        cls.logger.debug(f"trying to insert raceplan: {raceplan}")
        # Event can have one, and only, one raceplan:
        existing_rps: list[Raceplan] = []
        existing_rps = await RaceplansAdapter.get_raceplans_by_event_id(
            raceplan.event_id
        )
        cls.logger.debug(f"existing_rps: {existing_rps}")
        if len(existing_rps) > 0:
            msg = f'Event "{raceplan.event_id}!r" already has a raceplan.'
            raise RaceplanAllreadyExistError(msg)
        # insert new raceplan
        cls.logger.debug(f"new_raceplan: {raceplan}")
        result = await RaceplansAdapter.create_raceplan(raceplan)
        cls.logger.debug(f"inserted raceplan with id: {raceplan.id}")
        if result:
            return raceplan.id
        return None

    @classmethod
    async def update_raceplan(cls: Any, id_: UUID, raceplan: Raceplan) -> str | None:
        """Update raceplan function."""
        # get old document
        try:
            old_raceplan = await RaceplansAdapter.get_raceplan_by_id(id_)
        except RaceplanNotFoundError as e:
            raise e from e
        # update the raceplan if found:
        if raceplan.id != old_raceplan.id:
            msg = "Cannot change id for raceplan."
            raise IllegalValueError(msg)

        return await RaceplansAdapter.update_raceplan(id_, raceplan)

    @classmethod
    async def delete_raceplan(cls: Any, id_: UUID) -> str | None:
        """Delete raceplan function."""
        # get old document
        try:
            await RaceplansAdapter.get_raceplan_by_id(id_)
        except RaceplanNotFoundError as e:
            raise e from e
        # delete the document if found:
        return await RaceplansAdapter.delete_raceplan(id_)
