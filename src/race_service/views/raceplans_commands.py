"""Resource module for events resources."""
import os

from aiohttp import hdrs
from aiohttp.web import (
    Response,
    View,
)
from dotenv import load_dotenv
from multidict import MultiDict

from race_service.adapters import UsersAdapter
from race_service.commands import RaceplansCommands
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
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e

        # Execute command:
        event = await self.request.json()
        raceplan_id = await RaceplansCommands.generate_raceplan_for_event(db, event)
        headers = MultiDict({hdrs.LOCATION: f"{BASE_URL}/raceplans/{raceplan_id}"})
        return Response(status=201, headers=headers)
