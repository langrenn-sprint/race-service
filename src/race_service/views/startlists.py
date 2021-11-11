"""Resource module for startlists resources."""
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
from multidict import MultiDict

from race_service.adapters import UsersAdapter
from race_service.models import StartEntry, Startlist
from race_service.services import (
    CouldNotCreateStartlistException,
    IllegalValueException,
    StartEntriesService,
    StartlistAllreadyExistException,
    StartlistNotFoundException,
    StartlistsService,
)
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class StartlistsView(View):
    """Class representing startlists resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        if "eventId" in self.request.rel_url.query:
            event_id = self.request.rel_url.query["eventId"]
            startlists = await StartlistsService.get_startlist_by_event_id(db, event_id)
        else:
            startlists = await StartlistsService.get_all_startlists(db)
        list = []
        for _e in startlists:
            list.append(_e.to_dict())

        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    # TODO: users should not be able to post startlist, should post to /generate-startlist-for-event
    async def post(self) -> Response:
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        logging.debug(f"Got create request for startlist {body} of type {type(body)}")
        try:
            startlist = Startlist.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e
        try:
            startlist_id = await StartlistsService.create_startlist(db, startlist)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except (StartlistAllreadyExistException, CouldNotCreateStartlistException) as e:
            raise HTTPBadRequest(reason=str(e)) from e

        logging.debug(f"inserted document with startlist_id {startlist_id}")
        headers = MultiDict([(hdrs.LOCATION, f"{BASE_URL}/startlists/{startlist_id}")])

        return Response(status=201, headers=headers)


class StartlistView(View):
    """Class representing a single startlist resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        startlist_id = self.request.match_info["startlistId"]
        logging.debug(f"Got get request for startlist {startlist_id}")

        try:
            startlist: Startlist = await StartlistsService.get_startlist_by_id(
                db, startlist_id
            )
            start_entries: List[StartEntry] = []
            for start_entry_id in startlist.start_entries:
                start_entry = await StartEntriesService.get_start_entry_by_id(
                    db, start_entry_id
                )
                start_entries.append(start_entry)
            startlist.start_entries = start_entries  # type: ignore
        except StartlistNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        logging.debug(f"Got startlist: {startlist}")
        body = startlist.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        startlist_id = self.request.match_info["startlistId"]
        logging.debug(
            f"Got request-body {body} for {startlist_id} of type {type(body)}"
        )
        body = await self.request.json()
        logging.debug(f"Got put request for startlist {body} of type {type(body)}")
        try:
            startlist = Startlist.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await StartlistsService.update_startlist(db, startlist_id, startlist)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except StartlistNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        startlist_id = self.request.match_info["startlistId"]
        logging.debug(f"Got delete request for startlist {startlist_id}")

        try:
            await StartlistsService.delete_startlist(db, startlist_id)
        except StartlistNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
