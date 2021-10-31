"""Module for races service."""
import logging
from typing import Any, List, Optional
import uuid

from race_service.adapters import RacesAdapter
from race_service.models import IndividualSprintRace, IntervalStartRace, Race
from .exceptions import IllegalValueException


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class RaceNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RacesService:
    """Class representing a service for races."""

    @classmethod
    async def get_all_races(cls: Any, db: Any) -> List[Race]:
        """Get all races function."""
        races: List[Race] = []
        _races = await RacesAdapter.get_all_races(db)

        if _races:
            for _race in _races:
                if _race["datatype"] == "interval_start":
                    races.append(IntervalStartRace.from_dict(_race))
                elif _race["datatype"] == "individual_sprint":
                    races.append(IndividualSprintRace.from_dict(_race))
        return races

    @classmethod
    async def get_races_by_event_id(cls: Any, db: Any, event_id: str) -> List[Race]:
        """Get all races by event_id function."""
        races: List[Race] = []
        _races = await RacesAdapter.get_races_by_event_id(db, event_id)
        if _races:
            for _race in _races:
                if _race["datatype"] == "interval_start":
                    races.append(IntervalStartRace.from_dict(_race))
                elif _race["datatype"] == "individual_sprint":
                    races.append(IndividualSprintRace.from_dict(_race))
        return races

    @classmethod
    async def get_races_by_raceplan_id(
        cls: Any, db: Any, raceplan_id: str
    ) -> List[Race]:
        """Get all races by event_id function."""
        races: List[Race] = []
        _races = await RacesAdapter.get_races_by_raceplan_id(db, raceplan_id)

        if _races:
            for _race in _races:
                if _race["datatype"] == "interval_start":
                    races.append(IntervalStartRace.from_dict(_race))
                elif _race["datatype"] == "individual_sprint":
                    races.append(IndividualSprintRace.from_dict(_race))
        return races

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
        new_race = race.to_dict()
        logging.debug(f"new_race: {new_race}")
        result = await RacesAdapter.create_race(db, new_race)
        logging.debug(f"inserted race with id: {id}")
        if result:
            return id
        return None

    @classmethod
    async def get_race_by_id(cls: Any, db: Any, id: str) -> Race:
        """Get race by id function."""
        race = await RacesAdapter.get_race_by_id(db, id)
        # return the document if found:
        if race:
            if race["datatype"] == "interval_start":
                return IntervalStartRace.from_dict(race)
            elif race["datatype"] == "individual_sprint":
                return IndividualSprintRace.from_dict(race)
        raise RaceNotFoundException(f"Race with id {id} not found")

    @classmethod
    async def update_race(cls: Any, db: Any, id: str, race: Race) -> Optional[str]:
        """Update race function."""
        # get old document
        old_race = await RacesAdapter.get_race_by_id(db, id)
        # update the race if found:
        if old_race:
            if race.id != old_race["id"]:
                raise IllegalValueException("Cannot change id for race.")
            new_race = race.to_dict()
            result = await RacesAdapter.update_race(db, id, new_race)
            return result
        raise RaceNotFoundException(f"Race with id {id} not found.")

    @classmethod
    async def delete_race(cls: Any, db: Any, id: str) -> Optional[str]:
        """Delete race function."""
        # get old document
        race = await RacesAdapter.get_race_by_id(db, id)
        # delete the document if found:
        if race:
            result = await RacesAdapter.delete_race(db, id)
            return result
        raise RaceNotFoundException(f"Race with id {id} not found")


#   Validation:
async def validate_race(db: Any, race: Race) -> None:
    """Validate the race."""
    # Validate races:
    # TODO: validate race-properties.
    pass
