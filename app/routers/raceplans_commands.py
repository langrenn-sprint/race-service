"""Resource module for raceplan command resources."""

import logging
import os
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.adapters import (
    EventNotFoundError,
    RaceplanNotFoundError,
    RaceplansAdapter,
)
from app.authorization import Role, RoleChecker
from app.commands import (
    CompetitionFormatNotSupportedError,
    CouldNotCreateRaceError,
    CouldNotCreateRaceplanError,
    IllegalValueInRaceError,
    InconsistentValuesInRaceclassesError,
    InvalidDateFormatError,
    MissingPropertyError,
    NoRaceclassesInEventError,
    RaceplansCommands,
)
from app.services import (
    RaceplanAllreadyExistError,
)

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"

logger = logging.getLogger(__name__)

router = APIRouter(tags=["raceplans"])


class GenerateRaceplanCommand(BaseModel):
    """Request body for the generate raceplan command."""

    event_id: UUID


@router.post(
    "/raceplans/generate-raceplan-for-event",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def generate_raceplan_for_event(command: GenerateRaceplanCommand) -> Response:
    """Generate raceplan for the given event."""
    try:
        raceplan_id = await RaceplansCommands.generate_raceplan_for_event(
            command.event_id
        )
    except EventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except (
        CompetitionFormatNotSupportedError,
        CouldNotCreateRaceError,
        CouldNotCreateRaceplanError,
        IllegalValueInRaceError,
        InvalidDateFormatError,
        NoRaceclassesInEventError,
        MissingPropertyError,
        InconsistentValuesInRaceclassesError,
        RaceplanAllreadyExistError,
        ValueError,
    ) as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e
    headers = {"Location": f"{BASE_URL}/raceplans/{raceplan_id}"}
    return Response(status_code=HTTPStatus.CREATED, headers=headers)


@router.post(
    "/raceplans/{raceplan_id}/validate",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def validate_raceplan(raceplan_id: UUID) -> dict[int, list[str]]:
    """Validate the given raceplan."""
    # Fetch the raceplan:
    try:
        raceplan = await RaceplansAdapter.get_raceplan_by_id(raceplan_id)
    except RaceplanNotFoundError as e:  # pragma: no cover
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e

    # Validate
    try:
        return await RaceplansCommands.validate_raceplan(raceplan)
    except NoRaceclassesInEventError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e
