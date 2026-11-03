"""Module for race adapter."""

import logging
from typing import Any
from uuid import UUID

from app.models import IndividualSprintRace, IntervalStartRace, Race


class RaceNotFoundError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class NotSupportedRaceDatatypeError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RacesAdapter:
    """Class representing an adapter for races."""

    database: Any
    logger: logging.Logger

    @classmethod
    async def init(cls, database: Any) -> None:  # pragma: no cover
        """Initialize the class properties."""
        cls.database = database
        cls.logger = logging.getLogger("uvicorn.error")

    @classmethod
    async def get_all_races(
        cls: Any,
    ) -> list[IndividualSprintRace | IntervalStartRace]:  # pragma: no cover
        """Get all races function."""
        races: list[IndividualSprintRace | IntervalStartRace] = []

        cursor = cls.database.races_collection.find()

        for race in await cursor.to_list(None):
            if race["datatype"] == "interval_start":
                races.append(IntervalStartRace.model_validate(race))
            elif race["datatype"] == "individual_sprint":
                races.append(IndividualSprintRace.model_validate(race))
            else:
                msg = f"Datatype {race['datatype']} not supported."
                raise NotSupportedRaceDatatypeError(msg)

        return races

    @classmethod
    async def create_race(cls: Any, race: Race) -> str:  # pragma: no cover
        """Create race function."""
        return await cls.database.races_collection.insert_one(race.model_dump())

    @classmethod
    async def get_race_by_id(
        cls: Any, id_: UUID
    ) -> IndividualSprintRace | IntervalStartRace:  # pragma: no cover
        """Get race function."""
        _race = await cls.database.races_collection.find_one({"id": id_})
        if not _race:
            msg = f"Race with id {id_} not found."
            raise RaceNotFoundError(msg)

        race: IndividualSprintRace | IntervalStartRace
        if _race["datatype"] == "interval_start":
            race = IntervalStartRace.model_validate(_race)
        elif _race["datatype"] == "individual_sprint":
            race = IndividualSprintRace.model_validate(_race)
        else:
            msg = f"Datatype {_race['datatype']} not supported."
            raise NotSupportedRaceDatatypeError(msg)

        return race

    @classmethod
    async def get_races_by_event_id(
        cls: Any, event_id: UUID
    ) -> list[
        IndividualSprintRace | IntervalStartRace
    ]:  # pragma: no cover:  # pragma: no cover
        """Get races by event_id function."""
        races: list[IndividualSprintRace | IntervalStartRace] = []

        cursor = cls.database.races_collection.find({"event_id": event_id}).sort(
            [("order", 1)]
        )

        for race in await cursor.to_list(None):
            if race["datatype"] == "interval_start":
                races.append(IntervalStartRace.model_validate(race))
            elif race["datatype"] == "individual_sprint":
                races.append(IndividualSprintRace.model_validate(race))
            else:
                msg = f"Datatype {race['datatype']} not supported."
                raise NotSupportedRaceDatatypeError(msg)

        return races

    @classmethod
    async def get_races_by_event_id_and_raceclass(
        cls: Any, event_id: UUID, raceclass: str
    ) -> list[IndividualSprintRace | IntervalStartRace]:  # pragma: no cover
        """Get races by event_id and raceclass function."""
        races: list[IndividualSprintRace | IntervalStartRace] = []

        cursor = cls.database.races_collection.find(
            {
                "$and": [
                    {"event_id": event_id},
                    {"raceclass": raceclass},
                ]
            }
        ).sort([("order", 1)])

        for race in await cursor.to_list(None):
            if race["datatype"] == "interval_start":
                races.append(IntervalStartRace.model_validate(race))
            elif race["datatype"] == "individual_sprint":
                races.append(IndividualSprintRace.model_validate(race))
            else:
                msg = f"Datatype {race['datatype']} not supported."
                raise NotSupportedRaceDatatypeError(msg)

        return races

    @classmethod
    async def get_races_by_raceplan_id(
        cls: Any, raceplan_id: UUID
    ) -> list[IndividualSprintRace | IntervalStartRace]:  # pragma: no cover
        """Get races by raceplan_id function."""
        races: list[IndividualSprintRace | IntervalStartRace] = []

        cursor = cls.database.races_collection.find({"raceplan_id": raceplan_id}).sort(
            [("order", 1)]
        )

        for race in await cursor.to_list(None):
            if race["datatype"] == "interval_start":
                races.append(IntervalStartRace.model_validate(race))
            elif race["datatype"] == "individual_sprint":
                races.append(IndividualSprintRace.model_validate(race))
            else:
                msg = f"Datatype {race['datatype']} not supported."
                raise NotSupportedRaceDatatypeError(msg)

        return races

    @classmethod
    async def update_race(
        cls: Any, id_: UUID, race: Race
    ) -> str | None:  # pragma: no cover
        """Get race function."""
        return await cls.database.races_collection.replace_one(
            {"id": id_}, race.model_dump()
        )

    @classmethod
    async def delete_race(cls: Any, id_: UUID) -> str | None:  # pragma: no cover
        """Get race function."""
        return await cls.database.races_collection.delete_one({"id": id_})
