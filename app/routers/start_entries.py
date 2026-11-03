"""Resource module for start_entries resources."""

import logging
import os
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.adapters import (
    EventsAdapter,
    RaceNotFoundError,
    RaceplansAdapter,
    RacesAdapter,
    StartEntriesAdapter,
    StartEntryNotFoundError,
    StartlistNotFoundError,
    StartlistsAdapter,
)
from app.authorization import Role, RoleChecker
from app.models import (
    IndividualSprintRace,
    StartEntry,
)
from app.services import (
    CouldNotCreateStartEntryError,
    IllegalValueError,
    RaceplansService,
    RacesService,
    StartEntriesService,
    StartlistsService,
)

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["start-entries"])

ALLOWED_ROLES = [Role.ADMIN, Role.EVENT_ADMIN, Role.RACE_RESULT, Role.RACE_OFFICE]


@router.get("/races/{race_id}/start-entries")
async def get_start_entries(
    race_id: UUID,
    startlist_id: Annotated[
        UUID | None,
        Query(
            alias="startlistId",
            description="The startlist id to filter start-entries by.",
        ),
    ] = None,
) -> list[StartEntry]:
    """Get start-entries in a race."""
    if startlist_id is not None:
        return await StartEntriesAdapter.get_start_entries_by_race_id_and_startlist_id(
            race_id, startlist_id
        )
    return await StartEntriesAdapter.get_start_entries_by_race_id(race_id)


@router.post(
    "/races/{race_id}/start-entries",
    dependencies=[Depends(RoleChecker(ALLOWED_ROLES))],
)
async def create_start_entry(race_id: UUID, new_start_entry: StartEntry) -> Response:
    """Create the start_entry and add it to the race and startlist."""
    _ = race_id
    logger.debug(f"Got create request for start_entry {new_start_entry}")
    try:
        # First we need to get to the startlist the new start-entry is part of:
        startlist = await StartlistsAdapter.get_startlist_by_id(
            new_start_entry.startlist_id
        )
        # We need to check if the bib is already in the race, and
        # if the given starting-position is vacant, or
        # if there open starting-positions:
        race = await RacesAdapter.get_race_by_id(new_start_entry.race_id)
        start_entries_in_race = await StartEntriesAdapter.get_start_entries_by_race_id(
            race.id
        )
        bibs_in_race = [start_entry.bib for start_entry in start_entries_in_race]
        starting_positions_in_race = [
            start_entry.starting_position for start_entry in start_entries_in_race
        ]
        if not len(race.start_entries) < race.max_no_of_contestants:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Cannot add start-entry: race is full.",
            ) from None
        if new_start_entry.bib in bibs_in_race:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Cannot add start-entry: Bib {new_start_entry.bib} is already in the race.",
            ) from None
        if new_start_entry.starting_position in starting_positions_in_race:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=(
                    "Cannot add start-entry: Starting_position"
                    f"{new_start_entry.starting_position} is taken."
                ),
            ) from None

        # We can create the start-entry:
        start_entry_id = await StartEntriesService.create_start_entry(new_start_entry)

        # We need to add the start-entry to the race:
        race.start_entries.append(start_entry_id)
        race.no_of_contestants = len(race.start_entries)
        await RacesService.update_race(race.id, race)

        # If the race is in first round, we need to add to the raceplan's no_of_contestants:
        competition_format = await EventsAdapter.get_competition_format(
            event_id=race.event_id,
        )
        first_rounds = [
            competition_format["rounds_ranked_classes"][0],
            competition_format["rounds_non_ranked_classes"][0],
        ]
        if isinstance(race, IndividualSprintRace) and race.round in first_rounds:
            raceplan = await RaceplansAdapter.get_raceplan_by_id(race.raceplan_id)
            raceplan.no_of_contestants += 1
            await RaceplansService.update_raceplan(raceplan.id, raceplan)

        # We also need to add the start-entry to the startlist
        # and add the start_entry to it's no_of_contestants
        startlist.no_of_contestants += 1
        startlist.start_entries.append(start_entry_id)
        await StartlistsService.update_startlist(startlist.id, startlist)
    except (
        StartlistNotFoundError,
        RaceNotFoundError,
        CouldNotCreateStartEntryError,
    ) as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e
    logger.debug(f"inserted document with start_entry_id {start_entry_id}")

    headers = {"Location": f"{BASE_URL}/races/{race.id}/start-entries/{start_entry_id}"}
    return Response(status_code=HTTPStatus.CREATED, headers=headers)


@router.get("/races/{race_id}/start-entries/{start_entry_id}")
async def get_start_entry_by_id(race_id: UUID, start_entry_id: UUID) -> StartEntry:
    """Get start-entry by id."""
    _ = race_id
    logger.debug(f"Got get request for start_entry {start_entry_id}")
    try:
        start_entry = await StartEntriesAdapter.get_start_entry_by_id(start_entry_id)
    except StartEntryNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    logger.debug(f"Got start_entry: {start_entry}")
    return start_entry


@router.put(
    "/races/{race_id}/start-entries/{start_entry_id}",
    dependencies=[Depends(RoleChecker(ALLOWED_ROLES))],
)
async def update_start_entry(
    race_id: UUID, start_entry_id: UUID, start_entry: StartEntry
) -> Response:
    """Update start-entry."""
    _ = race_id
    logger.debug(f"Got put request for start_entry {start_entry_id}: {start_entry}")
    try:
        await StartEntriesService.update_start_entry(start_entry_id, start_entry)
    except IllegalValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except StartEntryNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete(
    "/races/{race_id}/start-entries/{start_entry_id}",
    dependencies=[Depends(RoleChecker(ALLOWED_ROLES))],
)
async def delete_start_entry(race_id: UUID, start_entry_id: UUID) -> Response:
    """Delete the start-entry, and remove it from the race and startlist."""
    _ = race_id
    logger.debug(f"Got delete request for start_entry {start_entry_id}")
    try:
        start_entry = await StartEntriesAdapter.get_start_entry_by_id(start_entry_id)
        # We need to remove the start-entry from the race containing the start-entry:
        try:
            race = await RacesAdapter.get_race_by_id(start_entry.race_id)
        except RaceNotFoundError as e:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=(
                    f"DB is inconsistent: cannot find race with id "
                    f"{start_entry.race_id} of start-entry with id {start_entry.id}"
                ),
            ) from e
        # Remove the start-entry from races start-entries
        race.start_entries = [
            _start_entry_id
            for _start_entry_id in race.start_entries
            if _start_entry_id != start_entry_id
        ]
        race.no_of_contestants = len(race.start_entries)
        await RacesService.update_race(race.id, race)

        # If the race is in first round, we need to subract from the raceplan's no_of_contestants:
        competition_format = await EventsAdapter.get_competition_format(
            event_id=race.event_id,
        )
        first_rounds = [
            competition_format["rounds_ranked_classes"][0],
            competition_format["rounds_non_ranked_classes"][0],
        ]
        if isinstance(race, IndividualSprintRace) and race.round in first_rounds:
            raceplan = await RaceplansAdapter.get_raceplan_by_id(race.raceplan_id)
            raceplan.no_of_contestants -= 1
            await RaceplansService.update_raceplan(raceplan.id, raceplan)

        # We also need to remove the start-entry from the startlist,
        # and subtract the start_entry from it's no_of_contestants
        try:
            startlist = await StartlistsAdapter.get_startlist_by_id(
                start_entry.startlist_id
            )
        except StartlistNotFoundError as e:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=(
                    f"DB is inconsistent: cannot find startlist with id "
                    f"{start_entry.startlist_id} of start-entry with id {start_entry.id}"
                ),
            ) from e
        startlist.start_entries = [
            _start_entry_id
            for _start_entry_id in startlist.start_entries
            if _start_entry_id != start_entry_id
        ]
        startlist.no_of_contestants += -1
        await StartlistsService.update_startlist(startlist.id, startlist)

        # We can finally delete the start-entry:
        await StartEntriesService.delete_start_entry(start_entry_id)
    except StartEntryNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    return Response(status_code=HTTPStatus.NO_CONTENT)
