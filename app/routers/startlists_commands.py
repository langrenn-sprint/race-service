"""Resource module for startlist command resources."""

import logging
import os
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.adapters import (
    ContestantsNotFoundError,
    EventNotFoundError,
    RaceclassesNotFoundError,
)
from app.authorization import Role, RoleChecker
from app.commands import (
    CompetitionFormatNotSupportedError,
    DuplicateRaceplansInEventError,
    InconsistentInputDataError,
    InconsistentValuesInContestantsError,
    InvalidDateFormatError,
    MissingPropertyError,
    NoRaceplanInEventError,
    NoRacesInRaceplanError,
    generate_startlist_for_event,
)
from app.services import StartlistAllreadyExistError

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["startlists"])


class GenerateStartlistCommand(BaseModel):
    """Request body for the generate startlist command."""

    event_id: UUID


@router.post(
    "/startlists/generate-startlist-for-event",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EVENT_ADMIN]))],
)
async def generate_startlist(command: GenerateStartlistCommand) -> Response:
    """Generate startlist for the given event."""
    try:
        startlist_id = await generate_startlist_for_event(command.event_id)
    except EventNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except (
        CompetitionFormatNotSupportedError,
        ContestantsNotFoundError,
        DuplicateRaceplansInEventError,
        InconsistentInputDataError,
        InconsistentValuesInContestantsError,
        InvalidDateFormatError,
        NoRaceplanInEventError,
        NoRacesInRaceplanError,
        MissingPropertyError,
        RaceclassesNotFoundError,
        StartlistAllreadyExistError,
    ) as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e)) from e

    headers = {"Location": f"{BASE_URL}/startlists/{startlist_id}"}
    return Response(status_code=HTTPStatus.CREATED, headers=headers)
