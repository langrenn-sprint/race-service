"""Resource module for race_results resources."""

import logging
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.adapters import (
    RaceNotFoundError,
    RaceResultNotFoundError,
    RaceResultsAdapter,
    RacesAdapter,
    TimeEventsAdapter,
)
from app.authorization import Role, RoleChecker
from app.models import (
    RaceResult,
    RaceResultWithTimeEvents,
)
from app.services import (
    IllegalValueError,
    RaceResultsService,
    RacesService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["race-results"])


@router.get("/races/{race_id}/race-results")
async def get_race_results(
    race_id: UUID,
    timing_point: Annotated[
        str | None,
        Query(
            alias="timingPoint",
            description="The timing point to filter race-results by.",
        ),
    ] = None,
    ids_only: Annotated[
        str | None,
        Query(
            alias="idsOnly",
            description=(
                "If given, the ranking-sequence will contain the ids of the"
                " time-events instead of the time-events."
            ),
        ),
    ] = None,
) -> list[RaceResultWithTimeEvents] | list[RaceResult]:
    """Get race-results for a race."""
    if timing_point is not None:
        race_results = (
            await RaceResultsAdapter.get_race_results_by_race_id_and_timing_point(
                race_id, timing_point
            )
        )
    else:
        race_results = await RaceResultsAdapter.get_race_results_by_race_id(race_id)
    # We expand references to time-events in race-results ranking-sequence:
    if ids_only:
        return race_results
    return [await expand_race_result(race_result) for race_result in race_results]


@router.get("/races/{race_id}/race-results/{race_result_id}")
async def get_race_result_by_id(
    race_id: UUID, race_result_id: UUID
) -> RaceResultWithTimeEvents:
    """Get race-result by id, with the ranking-sequence expanded."""
    _ = race_id
    logger.debug(f"Got get request for race_result {race_result_id}")
    try:
        race_result = await RaceResultsAdapter.get_race_result_by_id(race_result_id)
    except RaceResultNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    expanded_race_result = await expand_race_result(race_result)
    logger.debug(f"Got race_result: {expanded_race_result}")
    return expanded_race_result


@router.put(
    "/races/{race_id}/race-results/{race_result_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.RACE_RESULT]))],
)
async def update_race_result(
    race_id: UUID, race_result_id: UUID, race_result: RaceResult
) -> Response:
    """Update race-result."""
    _ = race_id
    logger.debug(f"Got put request for race_result {race_result_id}: {race_result}")
    try:
        await RaceResultsService.update_race_result(race_result_id, race_result)
    except IllegalValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except RaceResultNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/races/{race_id}/race-results/{race_result_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.RACE_RESULT]))],
)
async def delete_race_result(race_id: UUID, race_result_id: UUID) -> Response:
    """Delete the race-result, and remove it from the race."""
    _ = race_id
    logger.debug(f"Got delete request for race_result {race_result_id}")
    try:
        race_result = await RaceResultsAdapter.get_race_result_by_id(race_result_id)
        # We need to remove the race-result from the race containing the race-result:
        try:
            race = await RacesAdapter.get_race_by_id(race_result.race_id)
        except RaceNotFoundError as e:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=(
                    f"DB is inconsistent: cannot find race with id "
                    f"{race_result.race_id} of race-result with id {race_result.id}"
                ),
            ) from e
        del race.results[race_result.timing_point]
        await RacesService.update_race(race.id, race)

        # We can finally delete the race-result:
        await RaceResultsService.delete_race_result(race_result_id)
    except RaceResultNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


async def expand_race_result(race_result: RaceResult) -> RaceResultWithTimeEvents:
    """Replace references to time-events with time-events sorted on rank."""
    time_events = [
        await TimeEventsAdapter.get_time_event_by_id(time_event_id)
        for time_event_id in race_result.ranking_sequence
    ]
    time_events_sorted = sorted(
        time_events,
        key=lambda k: (
            k.rank is not None,
            k.rank != "",
            k.rank,
        ),
        reverse=False,
    )
    return RaceResultWithTimeEvents(
        **race_result.model_dump(exclude={"ranking_sequence"}),
        ranking_sequence=time_events_sorted,
    )
