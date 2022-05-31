"""Module for race-results service."""
from typing import Any, List, Optional
import uuid

from race_service.adapters import RaceResultsAdapter
from race_service.models import (
    RaceResult,
    RaceResultStatus,
    StartEntry,
    TimeEvent,
)
from .exceptions import IllegalValueException
from .races_service import RacesService
from .start_entries_service import StartEntriesService


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class RaceResultNotFoundException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeEventIsNotIdentifiableException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeEventDoesNotReferenceRaceException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantNotInStartEntriesException(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceResultsService:
    """Class representing a service for race_results."""

    @classmethod
    async def get_race_results_by_race_id(
        cls: Any, db: Any, race_id: str
    ) -> List[RaceResult]:
        """Get all race-results by race-id function."""
        race_results: List[RaceResult] = []
        _race_results = await RaceResultsAdapter.get_race_results_by_race_id(
            db, race_id
        )
        if _race_results:
            for _race_result in _race_results:
                race_results.append(RaceResult.from_dict(_race_result))
        return race_results

    @classmethod
    async def get_race_results_by_race_id_and_timing_point(
        cls: Any,
        db: Any,
        race_id: str,
        timing_point: str,
    ) -> List[RaceResult]:
        """Get race-result by id function."""
        race_results: List[RaceResult] = []
        _race_results = (
            await RaceResultsAdapter.get_race_results_by_race_id_and_timing_point(
                db, race_id, timing_point
            )
        )
        if _race_results:
            for _race_result in _race_results:
                race_results.append(RaceResult.from_dict(_race_result))
        return race_results

    @classmethod
    async def get_race_result_by_id(cls: Any, db: Any, id: str) -> RaceResult:
        """Get race-result by id function."""
        race_result = await RaceResultsAdapter.get_race_result_by_id(db, id)
        # return the document if found:
        if race_result:
            return RaceResult.from_dict(race_result)
        raise RaceResultNotFoundException(f"Race-result with id {id} not found")

    @classmethod
    async def update_race_result(
        cls: Any, db: Any, id: str, race_result: RaceResult
    ) -> Optional[str]:
        """Update race-result function."""
        # get old document
        old_race_result = await RaceResultsAdapter.get_race_result_by_id(db, id)
        # update the race_result if found:
        if old_race_result:
            if race_result.id != old_race_result["id"]:
                raise IllegalValueException("Cannot change id for race_result.")
            new_race_result = race_result.to_dict()
            result = await RaceResultsAdapter.update_race_result(
                db, id, new_race_result
            )
            return result
        raise RaceResultNotFoundException(f"ResultList with id {id} not found.")

    @classmethod
    async def delete_race_result(cls: Any, db: Any, id: str) -> Optional[str]:
        """Delete race-result function."""
        # get old document
        race_result = await RaceResultsAdapter.get_race_result_by_id(db, id)
        # delete the document if found:
        if race_result:
            result = await RaceResultsAdapter.delete_race_result(db, id)
            return result
        raise RaceResultNotFoundException(f"ResultList with id {id} not found")

    @classmethod
    async def add_time_event_to_race_result(
        cls: Any, db: Any, time_event: TimeEvent
    ) -> str:
        """Add time-event to race-result function."""
        if not time_event.id or len(time_event.id) == 0:
            raise TimeEventIsNotIdentifiableException(
                "Time-event has no id. Cannot proceed."
            ) from None

        if time_event.race_id and len(time_event.race_id) > 0:
            # Check if race exist:
            race = await RacesService.get_race_by_id(db, time_event.race_id)
            # Check if bib is in race's start-entries.
            start_entries: List[
                StartEntry
            ] = await StartEntriesService.get_start_entries_by_race_id(db, race.id)
            if time_event.bib not in [start_entry.bib for start_entry in start_entries]:
                raise ContestantNotInStartEntriesException(
                    f"Contestant with bib {time_event.bib} is not in race start-entries"
                )
            # Check if race_result exist for this timing-point:
            race_results = (
                await RaceResultsService.get_race_results_by_race_id_and_timing_point(
                    db, time_event.race_id, time_event.timing_point
                )
            )
            if len(race_results) == 0:
                # Create the race-result:
                race_result = RaceResult(
                    id=create_id(),
                    race_id=time_event.race_id,
                    timing_point=time_event.timing_point,
                    no_of_contestants=0,
                    ranking_sequence=[],
                    status=RaceResultStatus.UNOFFICIAL,
                )
                new_race_result = race_result.to_dict()
                await RaceResultsAdapter.create_race_result(db, new_race_result)
            else:
                race_result = race_results[0]
            # Add the time-event to the race-result's ranking-sequence:
            if time_event.id not in race_result.ranking_sequence:
                race_result.ranking_sequence.append(time_event.id)
                race_result.no_of_contestants += 1
                updated_race_result = race_result.to_dict()
                await RaceResultsAdapter.update_race_result(
                    db, race_result.id, updated_race_result
                )
            # Add the race_result_id to the race's results if it is not there already:
            if time_event.timing_point not in race.results:
                race.results[time_event.timing_point] = race_result.id
                await RacesService.update_race(db, race.id, race)

            return race_result.id
        else:
            raise TimeEventDoesNotReferenceRaceException(
                f"Time-event {time_event.id} does not have race reference."
            ) from None
