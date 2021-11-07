"""Resource module for start_entries resources."""
import json
import logging
import os

from aiohttp import hdrs
from aiohttp.web import (
    HTTPBadRequest,
    HTTPNotFound,
    HTTPUnprocessableEntity,
    Response,
    View,
)
from aiohttp.web_exceptions import HTTPInternalServerError
from dotenv import load_dotenv

from race_service.adapters import UsersAdapter
from race_service.models import (
    Race,
    StartEntry,
    Startlist,
)
from race_service.services import (
    CouldNotCreateStartEntryException,
    IllegalValueException,
    RacesService,
    StartEntriesService,
    StartEntryNotFoundException,
    StartlistsService,
)
from race_service.services.races_service import RaceNotFoundException
from race_service.services.startlists_service import StartlistNotFoundException
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class StartEntriesView(View):
    """Class representing start_entries resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "start_entry-admin"])
        except Exception as e:
            raise e from e

        if "startlistId" in self.request.rel_url.query:
            startlist_id = self.request.rel_url.query["startlistId"]
            start_entries = await StartEntriesService.get_start_entries_by_startlist_id(
                db, startlist_id
            )
        else:
            start_entries = await StartEntriesService.get_all_start_entries(db)
        list = []
        for start_entry in start_entries:
            list.append(start_entry.to_dict())

        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:  # noqa: C901
        """Create the start_entry and all the start_entries in it."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "start_entry-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        logging.debug(f"Got create request for start_entry {body} of type {type(body)}")
        try:
            if "id" not in body:
                body["id"] = ""  # create dummy id property
            start_entry = StartEntry.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            start_entry_id = await StartEntriesService.create_start_entry(
                db, start_entry
            )
            # We need to add the start-entry to the race:
            race: Race = await RacesService.get_race_by_id(db, start_entry.race_id)
            race.start_entries.append(start_entry_id)
            await RacesService.update_race(db, race.id, race)
            # TODO: We also need to remove the start-entry from the startlist
            # and add the start_entry to it's no_of_contestants
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        except CouldNotCreateStartEntryException as e:
            raise HTTPBadRequest(reason=e) from e
        logging.debug(f"inserted document with start_entry_id {start_entry_id}")
        headers = {
            hdrs.LOCATION: f"{BASE_URL}/races/{race.id}/start-entries/{start_entry_id}"
        }

        return Response(status=201, headers=headers)


class StartEntryView(View):
    """Class representing a single start_entry resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "start_entry-admin"])
        except Exception as e:
            raise e from e

        start_entry_id = self.request.match_info["startEntryId"]
        logging.debug(f"Got get request for start_entry {start_entry_id}")

        try:
            start_entry = await StartEntriesService.get_start_entry_by_id(
                db, start_entry_id
            )
        except StartEntryNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        logging.debug(f"Got start_entry: {start_entry}")
        body = start_entry.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "start_entry-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        start_entry_id = self.request.match_info["startEntryId"]
        logging.debug(
            f"Got request-body {body} for {start_entry_id} of type {type(body)}"
        )
        body = await self.request.json()
        logging.debug(f"Got put request for start_entry {body} of type {type(body)}")
        try:
            start_entry = StartEntry.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await StartEntriesService.update_start_entry(
                db, start_entry_id, start_entry
            )
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        except StartEntryNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete the reaceplan and all the start_entries in it."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "start_entry-admin"])
        except Exception as e:
            raise e from e

        start_entry_id = self.request.match_info["startEntryId"]
        logging.debug(f"Got delete request for start_entry {start_entry_id}")

        try:
            start_entry: StartEntry = await StartEntriesService.get_start_entry_by_id(
                db, start_entry_id
            )
            # We need to remove the start-entry from the race containing the start-entry:
            try:
                race: Race = await RacesService.get_race_by_id(db, start_entry.race_id)
            except RaceNotFoundException as e:
                raise HTTPInternalServerError(
                    reason=(
                        f"DB is inconsistent: cannot find race with id "
                        f"{start_entry.race_id} of start-entry with id {start_entry.id}"
                    )
                ) from e
            new_start_entries = [
                start_entry_id
                for start_entry_id in race.start_entries
                if start_entry_id != start_entry_id
            ]
            race.start_entries = new_start_entries
            await RacesService.update_race(db, race.id, race)

            # We also need to remove the start-entry from the startlist,
            # and subtract the start_entry from it's no_of_contestants
            try:
                startlist: Startlist = await StartlistsService.get_startlist_by_id(
                    db, start_entry.startlist_id
                )
            except StartlistNotFoundException as e:
                raise HTTPInternalServerError(
                    reason=(
                        f"DB is inconsistent: cannot find startlist with id"
                        f"{start_entry.startlist_id} of start-entry with id {start_entry.id}"
                    )
                ) from e
            new_start_entries = [
                start_entry_id
                for start_entry_id in startlist.start_entries
                if start_entry_id != start_entry_id
            ]
            startlist.start_entries = new_start_entries
            startlist.no_of_contestants += -1
            await StartlistsService.update_startlist(db, startlist.id, startlist)  # type: ignore

            # We can finally delete the start-entry:
            await StartEntriesService.delete_start_entry(db, start_entry_id)
        except StartEntryNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        return Response(status=204)