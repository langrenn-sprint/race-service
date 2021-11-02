"""Resource module for time_events resources."""
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

from race_service.adapters import UsersAdapter
from race_service.models import TimeEvent
from race_service.services import (
    IllegalValueException,
    TimeEventNotFoundException,
    TimeEventsService,
)
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class TimeEventsView(View):
    """Class representing time_events resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        if "eventId" in self.request.rel_url.query:
            event_id = self.request.rel_url.query["eventId"]
            time_events = await TimeEventsService.get_time_events_by_event_id(
                db, event_id
            )
        else:
            time_events = await TimeEventsService.get_all_time_events(db)
        list = []
        for _e in time_events:
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
        logging.debug(f"Got create request for time_event {body} of type {type(body)}")
        try:
            time_event = TimeEvent.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e
        try:
            time_event_id = await TimeEventsService.create_time_event(db, time_event)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        if time_event_id:
            logging.debug(f"inserted document with time_event_id {time_event_id}")
            headers = {hdrs.LOCATION: f"{BASE_URL}/time-events/{time_event_id}"}

            return Response(status=201, headers=headers)
        raise HTTPBadRequest() from None


class TimeEventView(View):
    """Class representing a single time_event resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        time_event_id = self.request.match_info["time_eventId"]
        logging.debug(f"Got get request for time_event {time_event_id}")

        try:
            time_event = await TimeEventsService.get_time_event_by_id(db, time_event_id)
        except TimeEventNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        logging.debug(f"Got time_event: {time_event}")
        body = time_event.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "time_event-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        time_event_id = self.request.match_info["time_eventId"]
        logging.debug(
            f"Got request-body {body} for {time_event_id} of type {type(body)}"
        )
        body = await self.request.json()
        logging.debug(f"Got put request for time_event {body} of type {type(body)}")
        try:
            time_event = TimeEvent.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await TimeEventsService.update_time_event(db, time_event_id, time_event)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        except TimeEventNotFoundException as e:
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

        time_event_id = self.request.match_info["time_eventId"]
        logging.debug(f"Got delete request for time_event {time_event_id}")

        try:
            await TimeEventsService.delete_time_event(db, time_event_id)
        except TimeEventNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        return Response(status=204)
