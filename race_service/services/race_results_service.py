"""Module for race-results service."""

import logging
import uuid
from typing import Any

from race_service.adapters import (
    RaceNotFoundError,
    RaceResultNotFoundError,
    RaceResultsAdapter,
    RacesAdapter,
    StartEntriesAdapter,
)
from race_service.models import (
    RaceResult,
    RaceResultStatus,
    StartEntry,
    TimeEvent,
)

from .races_service import IllegalValueError, RacesService


def create_id() -> str:  # pragma: no cover
    """Creates an uuid."""
    return str(uuid.uuid4())


class TimeEventIsNotIdentifiableError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TimeEventDoesNotReferenceRaceError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class ContestantNotInStartEntriesError(Exception):
    """Class representing custom exception for fetch method."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceResultsService:
    """Class representing a service for race_results."""

    logger = logging.getLogger(
        "race_service.services.race_results_service.RaceResultsService"
    )

    @classmethod
    async def update_race_result(
        cls: Any, db: Any, id_: str, race_result: RaceResult
    ) -> str | None:
        """Update race-result function."""
        # get old document
        try:
            old_race_result = await RaceResultsAdapter.get_race_result_by_id(db, id_)
        except RaceResultNotFoundError as e:
            raise e from e
        # update the race_result if found:
        if race_result.id != old_race_result.id:
            msg = "Cannot change id for race_result."
            raise IllegalValueError(msg)
        return await RaceResultsAdapter.update_race_result(db, id_, race_result)

    @classmethod
    async def delete_race_result(cls: Any, db: Any, id_: str) -> str | None:
        """Delete race-result function."""
        # get old document
        try:
            await RaceResultsAdapter.get_race_result_by_id(db, id_)
        except RaceResultNotFoundError as e:
            raise e from e
        # delete the document if found:
        return await RaceResultsAdapter.delete_race_result(db, id_)

    @classmethod
    async def add_time_event_to_race_result(
        cls: Any, db: Any, time_event: TimeEvent
    ) -> str:
        """Add time-event to race-result function."""
        if not time_event.id or len(time_event.id) == 0:
            msg = "Time-event has no id. Cannot proceed."
            raise TimeEventIsNotIdentifiableError(msg) from None

        if time_event.race_id and len(time_event.race_id) > 0:
            # Check if race exist:
            try:
                race = await RacesAdapter.get_race_by_id(db, time_event.race_id)
            except RaceNotFoundError as e:
                raise e from e
            # Check if bib is in race's start-entries.
            start_entries: list[
                StartEntry
            ] = await StartEntriesAdapter.get_start_entries_by_race_id(db, race.id)
            # For "Template" timing-point, we don't check if bib is in start-entries:
            if (
                time_event.timing_point.lower() != "Template".lower()
                and time_event.bib
                not in [start_entry.bib for start_entry in start_entries]
            ):
                msg = (
                    f'Error in time-event "{time_event.timing_point!r}": '
                    f"Contestant with bib {time_event.bib} is not in race start-entries."
                )
                raise ContestantNotInStartEntriesError(msg)
            # Check if race_result exist for this timing-point:
            race_results = (
                await RaceResultsAdapter.get_race_results_by_race_id_and_timing_point(
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
                    status=RaceResultStatus.UNOFFICIAL.value,
                )
                cls.logger.debug(f"Create race result for {race_result}")
                await RaceResultsAdapter.create_race_result(db, race_result)
            else:
                race_result = race_results[0]
            # Add the time-event to the race-result's ranking-sequence:
            if time_event.id not in race_result.ranking_sequence:
                race_result.ranking_sequence.append(time_event.id)
                race_result.no_of_contestants += 1
                await RaceResultsAdapter.update_race_result(
                    db, race_result.id, race_result
                )
            # Add the race_result_id to the race's results if it is not there already:
            if time_event.timing_point not in race.results:
                race.results[time_event.timing_point] = race_result.id
                await RacesService.update_race(db, race.id, race)

            return race_result.id
        msg = f"Time-event {time_event.id} does not have race reference."
        raise TimeEventDoesNotReferenceRaceError(msg) from None
