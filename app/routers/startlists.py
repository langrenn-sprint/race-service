"""Resource module for startlists resources."""

import logging
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.adapters import (
    RacesAdapter,
    StartEntriesAdapter,
    StartlistNotFoundError,
    StartlistsAdapter,
)
from app.authorization import Role, RoleChecker
from app.models import Startlist, StartlistWithStartEntries
from app.services import (
    RacesService,
    StartEntriesService,
    StartlistsService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["startlists"])


@router.get("/startlists")
async def get_startlists(
    event_id: Annotated[
        UUID | None,
        Query(
            alias="eventId",
            description=(
                "The event id to filter startlists by."
                " When given, start-entries are expanded."
            ),
        ),
    ] = None,
    bib: Annotated[
        int | None,
        Query(
            description=(
                "Only include start-entries with the given bib."
                " Only used together with eventId."
            ),
        ),
    ] = None,
) -> list[StartlistWithStartEntries] | list[Startlist]:
    """Get startlists, optionally filtered by event."""
    if event_id is None:
        return await StartlistsAdapter.get_all_startlists()

    startlists = await StartlistsAdapter.get_startlists_by_event_id(event_id)
    expanded_startlists: list[StartlistWithStartEntries] = []
    for startlist in startlists:
        start_entries = [
            await StartEntriesAdapter.get_start_entry_by_id(start_entry_id)
            for start_entry_id in startlist.start_entries
        ]
        if bib is not None:
            start_entries = [
                start_entry for start_entry in start_entries if start_entry.bib == bib
            ]
        expanded_startlists.append(
            StartlistWithStartEntries(
                **startlist.model_dump(exclude={"start_entries"}),
                start_entries=start_entries,
            )
        )
    return expanded_startlists


@router.get("/startlists/{startlist_id}")
async def get_startlist_by_id(startlist_id: UUID) -> StartlistWithStartEntries:
    """Get startlist by id, with start-entries expanded."""
    logger.debug(f"Got get request for startlist {startlist_id}")
    try:
        startlist = await StartlistsAdapter.get_startlist_by_id(startlist_id)
    except StartlistNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    start_entries = [
        await StartEntriesAdapter.get_start_entry_by_id(start_entry_id)
        for start_entry_id in startlist.start_entries
    ]
    logger.debug(f"Got startlist: {startlist}")
    return StartlistWithStartEntries(
        **startlist.model_dump(exclude={"start_entries"}),
        start_entries=start_entries,
    )


@router.delete(
    "/startlists/{startlist_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def delete_startlist(startlist_id: UUID) -> Response:
    """Delete startlist, and start-entries in it."""
    logger.debug(f"Got delete request for startlist {startlist_id}")
    try:
        startlist_to_be_deleted = await StartlistsAdapter.get_startlist_by_id(
            startlist_id
        )

        # First we need to remove all the start-entries:
        for start_entry_id in startlist_to_be_deleted.start_entries:
            await StartEntriesService.delete_start_entry(start_entry_id)

        # We also need to remove all start-entries in the event's races:
        races = await RacesAdapter.get_races_by_event_id(
            startlist_to_be_deleted.event_id
        )
        for race in races:
            race.start_entries = []
            await RacesService.update_race(race.id, race)

        # We can then delete the startlist:
        await StartlistsService.delete_startlist(startlist_id)
    except StartlistNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)
