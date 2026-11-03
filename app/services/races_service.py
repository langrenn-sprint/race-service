"""Module for races service."""

import logging
from typing import Any
from uuid import UUID

from app.adapters import RaceNotFoundError, RacesAdapter
from app.models import (
    Race,
)

from .exceptions import IllegalValueError


class RacesService:
    """Class representing a service for races."""

    logger = logging.getLogger("race_service.services.races_service.RacesService")

    @classmethod
    async def create_race(cls: Any, race: Race) -> UUID | None:
        """Create race function.

        Args:
            race (Race): a race instanse to be created

        Returns:
            Optional[UUID]: The id of the created race. None otherwise.
        """
        cls.logger.debug(f"trying to insert race: {race}")
        # Validation:
        await validate_race(race)
        # insert new race
        cls.logger.debug(f"new_race: {race}")
        result = await RacesAdapter.create_race(race)
        cls.logger.debug(f"inserted race with id: {race.id}")
        if result:
            return race.id
        return None

    @classmethod
    async def update_race(cls: Any, id_: UUID, race: Race) -> str | None:
        """Update race function."""
        # get old document
        try:
            old_race = await RacesAdapter.get_race_by_id(id_)
        except RaceNotFoundError as e:
            raise e from e
        # update the race if found:
        if race.id != old_race.id:
            msg = "Cannot change id for race."
            raise IllegalValueError(msg)
        cls.logger.debug(f"Updating race with following values:\n {race}")
        return await RacesAdapter.update_race(id_, race)

    @classmethod
    async def delete_race(cls: Any, id_: UUID) -> str | None:
        """Delete race function."""
        # get old document
        try:
            await RacesAdapter.get_race_by_id(id_)
        except RaceNotFoundError as e:
            raise e from e
        # delete the document if found:
        return await RacesAdapter.delete_race(id_)


#   Validation:
async def validate_race(race: Race) -> None:
    """Validate the race."""
    # Validate races:
