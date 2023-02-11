"""Module for raceplans service."""
import logging
from typing import Any, List, Optional
import uuid

from race_service.adapters import RaceplanNotFoundException, RaceplansAdapter
from race_service.models import Raceplan
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class RaceplanAllreadyExistException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceplansService:
    """Class representing a service for raceplans."""

    @classmethod
    async def create_raceplan(cls: Any, db: Any, raceplan: Raceplan) -> Optional[str]:
        """Create raceplan function.

        Args:
            db (Any): the db
            raceplan (Raceplan): a raceplan instanse to be created

        Returns:
            Optional[str]: The id of the created raceplan. None otherwise.

        Raises:
            IllegalValueException: input object has illegal values
            RaceplanAllreadyExistException: event can have zero or one plan
        """
        logging.debug(f"trying to insert raceplan: {raceplan}")
        # Event can have one, and only, one raceplan:
        existing_rps: List[Raceplan] = []
        existing_rps = await RaceplansAdapter.get_raceplans_by_event_id(
            db, raceplan.event_id
        )
        logging.debug(f"existing_rps: {existing_rps}")
        if len(existing_rps) > 0:
            raise RaceplanAllreadyExistException(
                f'Event "{raceplan.event_id}!r" already has a raceplan.'
            )
        if raceplan.id:
            raise IllegalValueException("Cannot create raceplan with input id.")
        # create ids:
        id = create_id()
        raceplan.id = id
        # insert new raceplan
        logging.debug(f"new_raceplan: {raceplan}")
        result = await RaceplansAdapter.create_raceplan(db, raceplan)
        logging.debug(f"inserted raceplan with id: {id}")
        if result:
            return id
        return None

    @classmethod
    async def update_raceplan(
        cls: Any, db: Any, id: str, raceplan: Raceplan
    ) -> Optional[str]:
        """Update raceplan function."""
        # get old document
        try:
            old_raceplan = await RaceplansAdapter.get_raceplan_by_id(db, id)
        except RaceplanNotFoundException as e:
            raise e
        # update the raceplan if found:
        if raceplan.id != old_raceplan.id:
            raise IllegalValueException("Cannot change id for raceplan.")

        result = await RaceplansAdapter.update_raceplan(db, id, raceplan)
        return result

    @classmethod
    async def delete_raceplan(cls: Any, db: Any, id: str) -> Optional[str]:
        """Delete raceplan function."""
        # get old document
        try:
            await RaceplansAdapter.get_raceplan_by_id(db, id)
        except RaceplanNotFoundException as e:
            raise e
        # delete the document if found:
        result = await RaceplansAdapter.delete_raceplan(db, id)
        return result
