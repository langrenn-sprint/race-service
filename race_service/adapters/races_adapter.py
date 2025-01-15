"""Module for race adapter."""

from typing import Any

from race_service.models import IndividualSprintRace, IntervalStartRace, Race


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

    @classmethod
    async def get_all_races(
        cls: Any, db: Any
    ) -> list[IndividualSprintRace | IntervalStartRace]:  # pragma: no cover
        """Get all races function."""
        races: list[IndividualSprintRace | IntervalStartRace] = []

        cursor = db.races_collection.find()

        for race in await cursor.to_list(None):
            if race["datatype"] == "interval_start":
                races.append(IntervalStartRace.from_dict(race))
            elif race["datatype"] == "individual_sprint":
                races.append(IndividualSprintRace.from_dict(race))
            else:
                msg = f"Datatype {race['datatype']} not supported."
                raise NotSupportedRaceDatatypeError(msg)

        return races

    @classmethod
    async def create_race(cls: Any, db: Any, race: Race) -> str:  # pragma: no cover
        """Create race function."""
        return await db.races_collection.insert_one(race.to_dict())

    @classmethod
    async def get_race_by_id(
        cls: Any, db: Any, id_: str
    ) -> IndividualSprintRace | IntervalStartRace:  # pragma: no cover
        """Get race function."""
        _race = await db.races_collection.find_one({"id": id_})
        if not _race:
            msg = f"Race with id {id_} not found."
            raise RaceNotFoundError(msg)

        race: IndividualSprintRace | IntervalStartRace
        if _race["datatype"] == "interval_start":
            race = IntervalStartRace.from_dict(_race)
        elif _race["datatype"] == "individual_sprint":
            race = IndividualSprintRace.from_dict(_race)
        else:
            msg = f"Datatype {_race['datatype']} not supported."
            raise NotSupportedRaceDatatypeError(msg)

        return race

    @classmethod
    async def get_races_by_event_id(
        cls: Any, db: Any, event_id: str
    ) -> list[
        IndividualSprintRace | IntervalStartRace
    ]:  # pragma: no cover:  # pragma: no cover
        """Get races by event_id function."""
        races: list[IndividualSprintRace | IntervalStartRace] = []

        cursor = db.races_collection.find({"event_id": event_id}).sort([("order", 1)])

        for race in await cursor.to_list(None):
            if race["datatype"] == "interval_start":
                races.append(IntervalStartRace.from_dict(race))
            elif race["datatype"] == "individual_sprint":
                races.append(IndividualSprintRace.from_dict(race))
            else:
                msg = f"Datatype {race['datatype']} not supported."
                raise NotSupportedRaceDatatypeError(msg)

        return races

    @classmethod
    async def get_races_by_event_id_and_raceclass(
        cls: Any, db: Any, event_id: str, raceclass: str
    ) -> list[IndividualSprintRace | IntervalStartRace]:  # pragma: no cover
        """Get races by event_id and raceclass function."""
        races: list[IndividualSprintRace | IntervalStartRace] = []

        cursor = db.races_collection.find(
            {
                "$and": [
                    {"event_id": event_id},
                    {"raceclass": raceclass},
                ]
            }
        ).sort([("order", 1)])

        for race in await cursor.to_list(None):
            if race["datatype"] == "interval_start":
                races.append(IntervalStartRace.from_dict(race))
            elif race["datatype"] == "individual_sprint":
                races.append(IndividualSprintRace.from_dict(race))
            else:
                msg = f"Datatype {race['datatype']} not supported."
                raise NotSupportedRaceDatatypeError(msg)

        return races

    @classmethod
    async def get_races_by_raceplan_id(
        cls: Any, db: Any, raceplan_id: str
    ) -> list[IndividualSprintRace | IntervalStartRace]:  # pragma: no cover
        """Get races by raceplan_id function."""
        races: list[IndividualSprintRace | IntervalStartRace] = []

        cursor = db.races_collection.find({"raceplan_id": raceplan_id}).sort(
            [("order", 1)]
        )

        for race in await cursor.to_list(None):
            if race["datatype"] == "interval_start":
                races.append(IntervalStartRace.from_dict(race))
            elif race["datatype"] == "individual_sprint":
                races.append(IndividualSprintRace.from_dict(race))
            else:
                msg = f"Datatype {race['datatype']} not supported."
                raise NotSupportedRaceDatatypeError(msg)

        return races

    @classmethod
    async def update_race(
        cls: Any, db: Any, id_: str, race: Race
    ) -> str | None:  # pragma: no cover
        """Get race function."""
        return await db.races_collection.replace_one({"id": id_}, race.to_dict())

    @classmethod
    async def delete_race(
        cls: Any, db: Any, id_: str
    ) -> str | None:  # pragma: no cover
        """Get race function."""
        return await db.races_collection.delete_one({"id": id_})
