"""Resource module for raceplan command resources."""

import json
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
    EventNotFoundError,
    RaceplanNotFoundError,
    RaceplansAdapter,
    UsersAdapter,
)
from race_service.commands import (
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
from race_service.services import (
    RaceplanAllreadyExistError,
)
from race_service.utils.jwt_utils import extract_token_from_request

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
            raise e from e

        # Execute command:
        request_body = await self.request.json()
        event_id = request_body["event_id"]
        try:
            raceplan_id = await RaceplansCommands.generate_raceplan_for_event(
                db, token, event_id
            )
        except EventNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
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
            raise HTTPBadRequest(reason=str(e)) from e
        headers = MultiDict([(hdrs.LOCATION, f"{BASE_URL}/raceplans/{raceplan_id}")])
        return Response(status=201, headers=headers)


class ValidateRaceplanView(View):
    """Class representing the validation of a given raceplan."""

    async def post(self) -> Response:
        """Post route function."""
        # Authorize:
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        assert token  # noqa: S101
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:  # pragma: no cover
            raise e from e

        raceplan_id = self.request.match_info["raceplanId"]

        # Fetch the raceplan:
        try:
            raceplan = await RaceplansAdapter.get_raceplan_by_id(db, raceplan_id)
        except RaceplanNotFoundError as e:  # pragma: no cover
            raise HTTPNotFound(reason=str(e)) from e

        # Validate
        try:
            result = await RaceplansCommands.validate_raceplan(db, token, raceplan)
        except NoRaceclassesInEventError as e:
            raise HTTPBadRequest(reason=str(e)) from e
        headers = MultiDict([(hdrs.CONTENT_TYPE, "application/json")])
        body = json.dumps(result, default=str, ensure_ascii=False)

        return Response(status=200, headers=headers, body=body)
