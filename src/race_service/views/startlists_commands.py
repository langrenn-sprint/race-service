"""Resource module for startlist command resources."""
import os

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
    ContestantsNotFoundException,
    EventNotFoundException,
    RaceclassesNotFoundException,
    UsersAdapter,
)
from race_service.commands import (
    CompetitionFormatNotSupportedException,
    DuplicateRaceplansInEventException,
    InconsistentInputDataException,
    InconsistentValuesInContestantsException,
    InvalidDateFormatException,
    MissingPropertyException,
    NoRaceplanInEventException,
    StartlistsCommands,
)
from race_service.services import StartlistAllreadyExistException
from .utils import extract_token_from_request

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
        assert token
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        # Execute command:
        request_body = await self.request.json()
        event_id = request_body["event_id"]
        try:
            startlist_id = await StartlistsCommands.generate_startlist_for_event(
                db, token, event_id
            )
        except EventNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        except (
            CompetitionFormatNotSupportedException,
            ContestantsNotFoundException,
            DuplicateRaceplansInEventException,
            InconsistentInputDataException,
            InconsistentValuesInContestantsException,
            InvalidDateFormatException,
            NoRaceplanInEventException,
            MissingPropertyException,
            RaceclassesNotFoundException,
            StartlistAllreadyExistException,
        ) as e:
            raise HTTPBadRequest(reason=e) from e
        headers = MultiDict({hdrs.LOCATION: f"{BASE_URL}/startlists/{startlist_id}"})
        return Response(status=201, headers=headers)