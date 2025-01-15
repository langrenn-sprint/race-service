"""Resource module for startlist command resources."""

import os
from json.decoder import JSONDecodeError

from aiohttp import hdrs
from aiohttp.web import (
    HTTPBadRequest,
    HTTPNotFound,
    Response,
    View,
)
from dotenv import load_dotenv
from multidict import MultiDict

from race_service.adapters import (
    ContestantsNotFoundError,
    EventNotFoundError,
    RaceclassesNotFoundError,
    UsersAdapter,
)
from race_service.commands import (
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
from race_service.services import StartlistAllreadyExistError
from race_service.utils.jwt_utils import extract_token_from_request

load_dotenv()

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class GenerateStartlistForEventView(View):
    """Class representing the generate startlist for event commands resources."""

    async def post(self) -> Response:
        """Post route function."""
        # Authorize:
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        assert token  # noqa: S101
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        # Execute command:
        try:
            request_body = await self.request.json()
        except JSONDecodeError as e:
            raise HTTPBadRequest(reason="Invalid request body") from e

        event_id = request_body["event_id"]
        try:
            startlist_id = await generate_startlist_for_event(db, token, event_id)
        except EventNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
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
            raise HTTPBadRequest(reason=str(e)) from e

        headers = MultiDict([(hdrs.LOCATION, f"{BASE_URL}/startlists/{startlist_id}")])
        return Response(status=201, headers=headers)
