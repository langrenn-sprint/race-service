"""Resource module for timeevents resources."""
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
from dotenv import load_dotenv
from multidict import MultiDict

from race_service.adapters import UsersAdapter
from race_service.models import Timeevent
from race_service.services import (
    IllegalValueException,
    TimeeventAllreadyExistException,
    TimeeventNotFoundException,
    TimeeventsService,
)
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class TimeeventsView(View):
    """Class representing timeevents resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        if "event-id" in self.request.rel_url.query:
            event_id = self.request.rel_url.query["event-id"]
            timeevents = await TimeeventsService.get_timeevent_by_event_id(db, event_id)
        else:
            timeevents = await TimeeventsService.get_all_timeevents(db)
        list = []
        for _e in timeevents:
            list.append(_e.to_dict())

        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        logging.debug(f"Got create request for timeevent {body} of type {type(body)}")
        try:
            timeevent = Timeevent.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e
        try:
            timeevent_id = await TimeeventsService.create_timeevent(db, timeevent)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        except TimeeventAllreadyExistException as e:
            raise HTTPBadRequest(reason=e) from e
        if timeevent_id:
            logging.debug(f"inserted document with timeevent_id {timeevent_id}")
            headers = MultiDict(
                {hdrs.LOCATION: f"{BASE_URL}/timeevents/{timeevent_id}"}
            )

            return Response(status=201, headers=headers)
        raise HTTPBadRequest() from None


class TimeeventView(View):
    """Class representing a single timeevent resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        timeevent_id = self.request.match_info["timeeventId"]
        logging.debug(f"Got get request for timeevent {timeevent_id}")

        try:
            timeevent = await TimeeventsService.get_timeevent_by_id(db, timeevent_id)
        except TimeeventNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        logging.debug(f"Got timeevent: {timeevent}")
        body = timeevent.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "timeevent-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        timeevent_id = self.request.match_info["timeeventId"]
        logging.debug(
            f"Got request-body {body} for {timeevent_id} of type {type(body)}"
        )
        body = await self.request.json()
        logging.debug(f"Got put request for timeevent {body} of type {type(body)}")
        try:
            timeevent = Timeevent.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await TimeeventsService.update_timeevent(db, timeevent_id, timeevent)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        except TimeeventNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        timeevent_id = self.request.match_info["timeeventId"]
        logging.debug(f"Got delete request for timeevent {timeevent_id}")

        try:
            await TimeeventsService.delete_timeevent(db, timeevent_id)
        except TimeeventNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        return Response(status=204)
