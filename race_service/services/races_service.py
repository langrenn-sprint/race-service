"""Module for races service."""
import logging
from typing import Any, Optional
import uuid

from race_service.adapters import RaceNotFoundException, RacesAdapter
from race_service.models import (
    Race,
)
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class RacesService:
    """Class representing a service for races."""

    @classmethod
    async def create_race(cls: Any, db: Any, race: Race) -> Optional[str]:
        """Create race function.

        Args:
            db (Any): the db
            race (Race): a race instanse to be created

        Returns:
            Optional[str]: The id of the created race. None otherwise.

        Raises:
            IllegalValueException: input object has illegal values
        """
        logging.debug(f"trying to insert race: {race}")
        # Validation:
        await validate_race(db, race)
        if hasattr(race, "id") and len(race.id) > 0:
            raise IllegalValueException("Cannot create race with input id.")
        # create ids:
        id = create_id()
        race.id = id
        # insert new race
        logging.debug(f"new_race: {race}")
        result = await RacesAdapter.create_race(db, race)
        logging.debug(f"inserted race with id: {id}")
        if result:
            return id
        return None

    @classmethod
    async def update_race(cls: Any, db: Any, id: str, race: Race) -> Optional[str]:
        """Update race function."""
        # get old document
        try:
            old_race = await RacesAdapter.get_race_by_id(db, id)
        except RaceNotFoundException as e:
            raise e from e
        # update the race if found:
        if race.id != old_race.id:
            raise IllegalValueException("Cannot change id for race.")
        logging.debug(f"Updating race with following values:\n {race}")
        result = await RacesAdapter.update_race(db, id, race)
        return result

    @classmethod
    async def delete_race(cls: Any, db: Any, id: str) -> Optional[str]:
        """Delete race function."""
        # get old document
        try:
            await RacesAdapter.get_race_by_id(db, id)
        except RaceNotFoundException as e:
            raise e from e
        # delete the document if found:
        result = await RacesAdapter.delete_race(db, id)
        return result


#   Validation:
async def validate_race(db: Any, race: Race) -> None:
    """Validate the race."""
    # Validate races:
    # TODO: validate race-properties.
    pass
