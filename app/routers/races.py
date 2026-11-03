"""Resource module for races resources."""

import logging
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.adapters import (
    NotSupportedRaceDatatypeError,
    RaceResultsAdapter,
    RacesAdapter,
    StartEntriesAdapter,
    TimeEventsAdapter,
)
from app.authorization import Role, RoleChecker
from app.models import (
    IndividualSprintRace,
    IndividualSprintRaceWithDetails,
    IntervalStartRace,
    IntervalStartRaceWithDetails,
    RaceResultWithTimeEvents,
    RaceUnion,
    RaceWithDetailsUnion,
    StartEntry,
)
from app.services import (
    IllegalValueError,
    RaceNotFoundError,
    RacesService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["races"])


@router.get("/races")
async def get_races(
    event_id: Annotated[
        UUID | None,
        Query(
            alias="eventId",
            description="The event id to filter races by.",
        ),
    ] = None,
    raceclass: Annotated[
        str | None,
        Query(
            description=(
                "The raceclass to filter races by. Only used together with eventId."
                " When given, start-entries and results are expanded."
            ),
        ),
    ] = None,
) -> list[RaceWithDetailsUnion] | list[RaceUnion]:
    """Get races, optionally filtered by event and raceclass."""
    if event_id is not None:
        if raceclass is not None:
            races = await RacesAdapter.get_races_by_event_id_and_raceclass(
                event_id, raceclass
            )
            return [await expand_race(race) for race in races]
        return await RacesAdapter.get_races_by_event_id(event_id)
    return await RacesAdapter.get_all_races()


@router.get("/races/{race_id}")
async def get_race_by_id(race_id: UUID) -> RaceWithDetailsUnion:
    """Get race by id, with start-entries and results expanded."""
    logger.debug(f"Got get request for race {race_id}")

    try:
        race = await RacesAdapter.get_race_by_id(race_id)
        expanded_race = await expand_race(race)
    except RaceNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except NotSupportedRaceDatatypeError as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    logger.debug(f"Got race: {expanded_race}")
    return expanded_race


@router.put(
    "/races/{race_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def update_race(race_id: UUID, race: RaceUnion) -> Response:
    """Update race."""
    logger.debug(f"Got put request for race {race_id}: {race}")
    try:
        await RacesService.update_race(race_id, race)
    except IllegalValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except RaceNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/races/{race_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def delete_race(race_id: UUID) -> Response:
    """Delete the race."""
    logger.debug(f"Got delete request for race {race_id}")
    try:
        await RacesService.delete_race(race_id)
    except RaceNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


async def expand_race(
    race: IndividualSprintRace | IntervalStartRace,
) -> IndividualSprintRaceWithDetails | IntervalStartRaceWithDetails:
    """Replace references to start-entries and results with the objects."""
    start_entries = await get_start_entries(race.start_entries)
    results = await get_race_results(race.results)
    race_dict = race.model_dump(exclude={"start_entries", "results"})
    if isinstance(race, IndividualSprintRace):
        return IndividualSprintRaceWithDetails(
            **race_dict, start_entries=start_entries, results=results
        )
    return IntervalStartRaceWithDetails(
        **race_dict, start_entries=start_entries, results=results
    )


async def get_start_entries(start_entry_ids: list[UUID]) -> list[StartEntry]:
    """Get the start entries."""
    start_entries: list[StartEntry] = [
        await StartEntriesAdapter.get_start_entry_by_id(start_entry_id)
        for start_entry_id in start_entry_ids
    ]
    # We sort the start-entries on starting_position:
    start_entries.sort(
        key=lambda k: (k.starting_position,),
        reverse=False,
    )
    return start_entries


async def get_race_results(
    race_results: dict[str, UUID],
) -> dict[str, RaceResultWithTimeEvents]:
    """Get the race results with time-events sorted on rank."""
    results: dict[str, RaceResultWithTimeEvents] = {}
    for key, race_result_id in race_results.items():
        if key.lower() != "Template".lower():  # We skip the template
            race_result = await RaceResultsAdapter.get_race_result_by_id(race_result_id)
            ranking_sequence = [
                await TimeEventsAdapter.get_time_event_by_id(time_event_id)
                for time_event_id in race_result.ranking_sequence
            ]
            # We sort the time-events on rank:
            ranking_sequence_sorted = sorted(
                ranking_sequence,
                key=lambda k: (
                    k.rank is not None,
                    k.rank != "",
                    k.rank,
                ),
                reverse=False,
            )
            results[key] = RaceResultWithTimeEvents(
                **race_result.model_dump(exclude={"ranking_sequence"}),
                ranking_sequence=ranking_sequence_sorted,
            )
    return results
