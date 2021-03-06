"""Resource module for raceplan command resources."""
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
    EventNotFoundException,
    UsersAdapter,
)
from race_service.commands import (
    CompetitionFormatNotSupportedException,
    CouldNotCreateRaceException,
    CouldNotCreateRaceplanException,
    InconsistentValuesInRaceclassesException,
    InvalidDateFormatException,
    MissingPropertyException,
    NoRaceclassesInEventException,
    RaceplansCommands,
)
from race_service.services import RaceplanAllreadyExistException
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class GenerateRaceplanForEventView(View):
    """Class representing the generate raceplan for event commands resources."""

    async def post(self) -> Response:
        """Post route function."""
        # Authorize:
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        assert token  # noqa: S101
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        # Execute command:
        request_body = await self.request.json()
        event_id = request_body["event_id"]
        try:
            raceplan_id = await RaceplansCommands.generate_raceplan_for_event(
                db, token, event_id
            )
        except EventNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        except (
            CompetitionFormatNotSupportedException,
            CouldNotCreateRaceException,
            CouldNotCreateRaceplanException,
            InvalidDateFormatException,
            NoRaceclassesInEventException,
            MissingPropertyException,
            InconsistentValuesInRaceclassesException,
            RaceplanAllreadyExistException,
            ValueError,
        ) as e:
            raise HTTPBadRequest(reason=str(e)) from e
        headers = MultiDict([(hdrs.LOCATION, f"{BASE_URL}/raceplans/{raceplan_id}")])
        return Response(status=201, headers=headers)
