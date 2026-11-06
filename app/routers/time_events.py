"""Resource module for time_events resources."""

import logging
from datetime import datetime
from http import HTTPStatus
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.adapters import (
    EventsAdapter,
    RaceNotFoundError,
    RaceResultsAdapter,
    TimeEventNotFoundError,
    TimeEventsAdapter,
)
from app.authorization import Role, require_roles
from app.models import Changelog, TimeEvent
from app.services import (
    ContestantNotInStartEntriesError,
    CouldNotCreateTimeEventError,
    IllegalValueError,
    RaceResultsService,
    TimeEventAllreadyExistError,
    TimeEventDoesNotReferenceRaceError,
    TimeEventsService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["time-events"])

ALLOWED_ROLES = [Role.ADMIN, Role.EVENT_ADMIN, Role.RESULT_ADMIN]


@router.get("/time-events")
async def get_time_events(
    event_id: Annotated[
        UUID | None,
        Query(alias="eventId", description="The event id to filter time-events by."),
    ] = None,
    timing_point: Annotated[
        str | None,
        Query(
            alias="timingPoint",
            description="The timing point to filter by. Only used together with eventId.",
        ),
    ] = None,
    bib: Annotated[
        int | None,
        Query(description="The bib to filter by. Only used together with eventId."),
    ] = None,
    race_id: Annotated[
        UUID | None,
        Query(
            alias="raceId",
            description="The race id to filter time-events by. Ignored if eventId is given.",
        ),
    ] = None,
) -> list[TimeEvent]:
    """Get time-events."""
    if event_id is not None:
        if timing_point is not None:
            return await TimeEventsAdapter.get_time_events_by_event_id_and_timing_point(
                event_id, timing_point
            )
        if bib is not None:
            return await TimeEventsAdapter.get_time_events_by_event_id_and_bib(
                event_id, bib
            )
        return await TimeEventsAdapter.get_time_events_by_event_id(event_id)
    if race_id is not None:
        return await TimeEventsAdapter.get_time_events_by_race_id(race_id)
    return await TimeEventsAdapter.get_all_time_events()


@router.post(
    "/time-events",
    dependencies=[require_roles(*ALLOWED_ROLES)],
)
async def create_time_event(time_event: TimeEvent) -> TimeEvent:
    """Create time-event, and add it to the race-result of the race."""
    logger.debug(f"Got create request for time_event {time_event}")
    try:
        time_event_id = await TimeEventsService.create_time_event(time_event)
        time_event.id = time_event_id
        try:
            # Add the time-event ref to the race-result for the race:
            await RaceResultsService.add_time_event_to_race_result(time_event)
            time_event.status = "OK"
        except (
            RaceNotFoundError,
            TimeEventDoesNotReferenceRaceError,
            ContestantNotInStartEntriesError,
        ) as e:
            time_event.status = "Error"
            if not time_event.changelog:
                time_event.changelog = []
            event = await EventsAdapter.get_event_by_id(event_id=time_event.event_id)
            time_event.changelog.append(
                Changelog(
                    timestamp=datetime.now(ZoneInfo(event["timezone"])),
                    user_id="race_service",
                    comment=str(e),
                )
            )
        await TimeEventsService.update_time_event(time_event.id, time_event)
    except IllegalValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except (
        CouldNotCreateTimeEventError,
        TimeEventAllreadyExistError,
    ) as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e
    logger.debug(f"inserted document with time_event_id {time_event_id}")
    return time_event


@router.get("/time-events/{time_event_id}")
async def get_time_event_by_id(time_event_id: UUID) -> TimeEvent:
    """Get time-event by id."""
    logger.debug(f"Got get request for time_event {time_event_id}")
    try:
        time_event = await TimeEventsAdapter.get_time_event_by_id(time_event_id)
    except TimeEventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    logger.debug(f"Got time_event: {time_event}")
    return time_event


@router.put(
    "/time-events/{time_event_id}",
    dependencies=[require_roles(*ALLOWED_ROLES)],
)
async def update_time_event(time_event_id: UUID, time_event: TimeEvent) -> Response:
    """Update time-event."""
    logger.debug(f"Got put request for time_event {time_event_id}: {time_event}")
    try:
        await TimeEventsService.update_time_event(time_event_id, time_event)
    except IllegalValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except TimeEventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/time-events/{time_event_id}",
    dependencies=[require_roles(*ALLOWED_ROLES)],
)
async def delete_time_event(time_event_id: UUID) -> Response:
    """Delete time-event and also remove it from race-result."""
    logger.debug(f"Got delete request for time_event {time_event_id}")
    try:
        time_event = await TimeEventsAdapter.get_time_event_by_id(time_event_id)
        # First we try to remove time-event from race-result's ranking-sequence:
        if time_event.race_id:
            race_results = (
                await RaceResultsAdapter.get_race_results_by_race_id_and_timing_point(
                    time_event.race_id, time_event.timing_point
                )
            )
            for race_result in race_results:
                # We try to remove time-event and subtract counter:
                try:
                    race_result.ranking_sequence.remove(time_event_id)
                    race_result.no_of_contestants -= 1
                    # Update race-result:
                    await RaceResultsService.update_race_result(
                        race_result.id, race_result
                    )
                except ValueError:  # pragma: no cover
                    pass  # We do not care if it is not there
        # We are ready to remove the time-event
        await TimeEventsService.delete_time_event(time_event_id)
    except TimeEventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)
