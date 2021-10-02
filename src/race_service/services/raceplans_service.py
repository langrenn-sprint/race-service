"""Module for raceplans service."""
import logging
from typing import Any, List, Optional
import uuid

from race_service.adapters import RaceplansAdapter
from race_service.models import Raceplan
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class RaceplanNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceplanAllreadyExistException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceplansService:
    """Class representing a service for raceplans."""

    @classmethod
    async def get_all_raceplans(cls: Any, db: Any) -> List[Raceplan]:
        """Get all raceplans function."""
        raceplans: List[Raceplan] = []
        _raceplans = await RaceplansAdapter.get_all_raceplans(db)
        for e in _raceplans:
            raceplans.append(Raceplan.from_dict(e))
        return raceplans

    @classmethod
    async def get_raceplan_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> List[Raceplan]:
        """Get all raceplans by event_id function."""
        raceplans: List[Raceplan] = []
        _raceplan = await RaceplansAdapter.get_raceplan_by_event_id(db, event_id)
        if _raceplan:
            raceplans.append(Raceplan.from_dict(_raceplan))
        return raceplans

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
        existing_rp = await RaceplansAdapter.get_raceplan_by_event_id(
            db, raceplan.event_id
        )
        if existing_rp:
            raise RaceplanAllreadyExistException(
                f'Event "{raceplan.event_id}" already has a raceplan.'
            )
        # Validation:
        await validate_raceplan(db, raceplan)
        if raceplan.id:
            raise IllegalValueException("Cannot create raceplan with input id.")
        # create id
        id = create_id()
        raceplan.id = id
        # insert new raceplan
        new_raceplan = raceplan.to_dict()
        logging.debug(f"new_raceplan: {new_raceplan}")
        result = await RaceplansAdapter.create_raceplan(db, new_raceplan)
        logging.debug(f"inserted raceplan with id: {id}")
        if result:
            return id
        return None

    @classmethod
    async def get_raceplan_by_id(cls: Any, db: Any, id: str) -> Raceplan:
        """Get raceplan function."""
        raceplan = await RaceplansAdapter.get_raceplan_by_id(db, id)
        # return the document if found:
        if raceplan:
            return Raceplan.from_dict(raceplan)
        raise RaceplanNotFoundException(f"Raceplan with id {id} not found")

    @classmethod
    async def update_raceplan(
        cls: Any, db: Any, id: str, raceplan: Raceplan
    ) -> Optional[str]:
        """Get raceplan function."""
        # get old document
        old_raceplan = await RaceplansAdapter.get_raceplan_by_id(db, id)
        # update the raceplan if found:
        if old_raceplan:
            if raceplan.id != old_raceplan["id"]:
                raise IllegalValueException("Cannot change id for raceplan.")
            new_raceplan = raceplan.to_dict()
            result = await RaceplansAdapter.update_raceplan(db, id, new_raceplan)
            return result
        raise RaceplanNotFoundException(f"Raceplan with id {id} not found.")

    @classmethod
    async def delete_raceplan(cls: Any, db: Any, id: str) -> Optional[str]:
        """Get raceplan function."""
        # get old document
        raceplan = await RaceplansAdapter.get_raceplan_by_id(db, id)
        # delete the document if found:
        if raceplan:
            result = await RaceplansAdapter.delete_raceplan(db, id)
            return result
        raise RaceplanNotFoundException(f"Raceplan with id {id} not found")


#   Validation:
async def validate_raceplan(db: Any, raceplan: Raceplan) -> None:
    """Validate the raceplan."""
    # Validate races:
    # TODO: validate race-properties.
    if raceplan.races:
        for _race in raceplan.races:
            pass
