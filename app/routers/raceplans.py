"""Resource module for raceplans resources."""

import logging
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.adapters import (
    RaceNotFoundError,
    RaceplanNotFoundError,
    RaceplansAdapter,
    RacesAdapter,
)
from app.authorization import Role, RoleChecker
from app.models import (
    IndividualSprintRace,
    IntervalStartRace,
    Raceplan,
    RaceplanWithRaces,
)
from app.services import (
    IllegalValueError,
    RaceplansService,
    RacesService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["raceplans"])


@router.get("/raceplans")
async def get_raceplans(
    event_id: Annotated[
        UUID | None,
        Query(
            alias="eventId",
            description="The event id to filter raceplans by.",
        ),
    ] = None,
) -> list[Raceplan]:
    """Get all raceplans, optionally filtered by event."""
    if event_id is not None:
        return await RaceplansAdapter.get_raceplans_by_event_id(event_id)
    return await RaceplansAdapter.get_all_raceplans()


@router.get("/raceplans/{raceplan_id}")
async def get_raceplan_by_id(raceplan_id: UUID) -> RaceplanWithRaces:
    """Get raceplan by id, with races expanded."""
    logger.debug(f"Got get request for raceplan {raceplan_id}")

    try:
        raceplan = await RaceplansAdapter.get_raceplan_by_id(raceplan_id)
    except RaceplanNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    # Replace list of race-ids with corresponding races:
    races: list[IndividualSprintRace | IntervalStartRace] = [
        await RacesAdapter.get_race_by_id(race_id) for race_id in raceplan.races
    ]
    races.sort(key=lambda k: (k.order,), reverse=False)
    logger.debug(f"Got raceplan: {raceplan}")
    return RaceplanWithRaces(
        **raceplan.model_dump(exclude={"races"}),
        races=races,
    )


@router.put(
    "/raceplans/{raceplan_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def update_raceplan(raceplan_id: UUID, raceplan: Raceplan) -> Response:
    """Update raceplan."""
    logger.debug(f"Got put request for raceplan {raceplan_id}: {raceplan}")
    try:
        await RaceplansService.update_raceplan(raceplan_id, raceplan)
    except IllegalValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except RaceplanNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/raceplans/{raceplan_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def delete_raceplan(raceplan_id: UUID) -> Response:
    """Delete the raceplan and all the races in it."""
    logger.debug(f"Got delete request for raceplan {raceplan_id}")
    try:
        raceplan = await RaceplansAdapter.get_raceplan_by_id(raceplan_id)
        for race_id in raceplan.races:
            await RacesService.delete_race(race_id)
        await RaceplansService.delete_raceplan(raceplan_id)
    except (RaceplanNotFoundError, RaceNotFoundError) as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)
