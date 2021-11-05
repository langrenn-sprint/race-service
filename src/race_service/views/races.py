"""Resource module for races resources."""
import json
import logging
import os
from typing import List

from aiohttp import hdrs
from aiohttp.web import (
    HTTPBadRequest,
    HTTPNotFound,
    HTTPUnprocessableEntity,
    Response,
    View,
)
from dotenv import load_dotenv

from race_service.adapters import UsersAdapter
from race_service.models import (
    IndividualSprintRace,
    IntervalStartRace,
    Race,
    StartEntry,
)
from race_service.services import (
    IllegalValueException,
    RaceNotFoundException,
    RacesService,
    StartEntriesService,
)
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class RacesView(View):
    """Class representing races resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "race-admin"])
        except Exception as e:
            raise e from e

        if "eventId" in self.request.rel_url.query:
            event_id = self.request.rel_url.query["eventId"]
            races = await RacesService.get_races_by_event_id(db, event_id)
        else:
            races = await RacesService.get_all_races(db)
        list = []
        for race in races:
            list.append(race.to_dict())

        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    # TODO: users should not be able to post race, should post to /generate-raceplan-for-event
    async def post(self) -> Response:  # noqa: C901
        """Create the race and all the races in it."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "race-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        logging.debug(f"Got create request for race {body} of type {type(body)}")
        try:
            if "id" not in body:
                body["id"] = ""  # create dummy id property
            if body["datatype"] == "individual_sprint":
                race = IndividualSprintRace.from_dict(body)
            elif body["datatype"] == "interval_start":
                race = IntervalStartRace.from_dict(body)
            else:
                raise HTTPBadRequest(
                    reason=f'Race of type "{body["datatype"]}" not supported.'
                )
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            race_id = await RacesService.create_race(db, race)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        if race_id:
            logging.debug(f"inserted document with race_id {race_id}")
            headers = {hdrs.LOCATION: f"{BASE_URL}/races/{race_id}"}

            return Response(status=201, headers=headers)
        raise HTTPBadRequest() from None


class RaceView(View):
    """Class representing a single race resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "race-admin"])
        except Exception as e:
            raise e from e

        race_id = self.request.match_info["raceId"]
        logging.debug(f"Got get request for race {race_id}")

        try:
            race = await RacesService.get_race_by_id(db, race_id)
            start_entries: List[StartEntry] = []
            for start_entry_id in race.start_entries:
                start_entry: StartEntry = (
                    await StartEntriesService.get_start_entry_by_id(db, start_entry_id)
                )
                start_entries.append(start_entry)
            race.start_entries = start_entries  # type: ignore
        except RaceNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        logging.debug(f"Got race: {race}")
        body = race.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "race-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        race_id = self.request.match_info["raceId"]
        logging.debug(f"Got request-body {body} for {race_id} of type {type(body)}")
        body = await self.request.json()
        logging.debug(f"Got put request for race {body} of type {type(body)}")
        try:
            race = Race.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await RacesService.update_race(db, race_id, race)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        except RaceNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete the reaceplan and all the races in it."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "race-admin"])
        except Exception as e:
            raise e from e

        race_id = self.request.match_info["raceId"]
        logging.debug(f"Got delete request for race {race_id}")

        try:
            await RacesService.delete_race(db, race_id)
        except RaceNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        return Response(status=204)
