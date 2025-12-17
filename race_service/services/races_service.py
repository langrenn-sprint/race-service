"""Module for races service."""

import logging
import uuid
from typing import Any

from race_service.adapters import RaceNotFoundError, RacesAdapter
from race_service.models import (
    Race,
)

from .exceptions import IllegalValueError


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class RacesService:
    """Class representing a service for races."""

    logger = logging.getLogger("race_service.services.races_service.RacesService")

    @classmethod
    async def create_race(cls: Any, db: Any, race: Race) -> str | None:
        """Create race function.

        Args:
            db (Any): the db
            race (Race): a race instanse to be created

        Returns:
            Optional[str]: The id of the created race. None otherwise.

        Raises:
            IllegalValueError: input object has illegal values
        """
        cls.logger.debug(f"trying to insert race: {race}")
        # Validation:
        await validate_race(db, race)
        if hasattr(race, "id") and len(race.id) > 0:
            msg = "Cannot create race with input id."
            raise IllegalValueError(msg)
        # create ids:
        race_id = create_id()
        race.id = race_id
        # insert new race
        cls.logger.debug(f"new_race: {race}")
        result = await RacesAdapter.create_race(db, race)
        cls.logger.debug(f"inserted race with id: {race_id}")
        if result:
            return race_id
        return None

    @classmethod
    async def update_race(cls: Any, db: Any, id_: str, race: Race) -> str | None:
        """Update race function."""
        # get old document
        try:
            old_race = await RacesAdapter.get_race_by_id(db, id_)
        except RaceNotFoundError as e:
            raise e from e
        # update the race if found:
        if race.id != old_race.id:
            msg = "Cannot change id for race."
            raise IllegalValueError(msg)
        cls.logger.debug(f"Updating race with following values:\n {race}")
        return await RacesAdapter.update_race(db, id_, race)

    @classmethod
    async def delete_race(cls: Any, db: Any, id_: str) -> str | None:
        """Delete race function."""
        # get old document
        try:
            await RacesAdapter.get_race_by_id(db, id_)
        except RaceNotFoundError as e:
            raise e from e
        # delete the document if found:
        return await RacesAdapter.delete_race(db, id_)


#   Validation:
async def validate_race(db: Any, race: Race) -> None:
    """Validate the race."""
    # Validate races:
