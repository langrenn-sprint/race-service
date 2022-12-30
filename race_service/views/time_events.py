"""Resource module for time_events resources."""
from datetime import datetime
import json
import logging
import os
from typing import List

from aiohttp.web import (
    HTTPBadRequest,
    HTTPNotFound,
    HTTPUnprocessableEntity,
    Response,
    View,
)
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from race_service.adapters import EventsAdapter, UsersAdapter
from race_service.models import Changelog, TimeEvent
from race_service.models.race_model import RaceResult
from race_service.services import (
    ContestantNotInStartEntriesException,
    CouldNotCreateTimeEventException,
    IllegalValueException,
    RaceNotFoundException,
    RaceResultsService,
    TimeEventAllreadyExistException,
    TimeEventDoesNotReferenceRaceException,
    TimeEventIsNotIdentifiableException,
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

        if "eventId" in self.request.rel_url.query:
            event_id = self.request.rel_url.query["eventId"]
            if "timingPoint" in self.request.rel_url.query:
                timing_point = self.request.rel_url.query["timingPoint"]
                time_events = await TimeEventsService.get_time_events_by_event_id_and_timing_point(
                    db, event_id, timing_point
                )
            else:
                time_events = await TimeEventsService.get_time_events_by_event_id(
                    db, event_id
                )
        elif "raceId" in self.request.rel_url.query:
            race_id = self.request.rel_url.query["raceId"]
            time_events = await TimeEventsService.get_time_events_by_race_id(
                db, race_id
            )
        else:
            time_events = await TimeEventsService.get_all_time_events(db)
        list = []
        for _e in time_events:
            list.append(_e.to_dict())

        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:  # noqa: C901
        """Post route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(
                token, roles=["admin", "event-admin", "race-result"]
            )
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
            time_event.id = time_event_id
            try:
                # Add the time-event ref to the race-result for the race:
                await RaceResultsService.add_time_event_to_race_result(db, time_event)
                time_event.status = "OK"
            except (
                RaceNotFoundException,
                TimeEventDoesNotReferenceRaceException,
                TimeEventIsNotIdentifiableException,
                ContestantNotInStartEntriesException,
            ) as e:
                time_event.status = "Error"
                if not time_event.changelog:
                    time_event.changelog = []
                event = await EventsAdapter.get_event_by_id(
                    token=token, event_id=time_event.event_id  # type: ignore
                )
                time_event.changelog.append(
                    Changelog(
                        timestamp=datetime.now(ZoneInfo(event["timezone"])),
                        user_id="race_service",
                        comment=str(e),
                    )
                )
            await TimeEventsService.update_time_event(db, time_event.id, time_event)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except (
            CouldNotCreateTimeEventException,
            TimeEventAllreadyExistException,
        ) as e:
            raise HTTPBadRequest(reason=str(e)) from e
        logging.debug(f"inserted document with time_event_id {time_event_id}")

        body = time_event.to_json()
        return Response(status=200, body=body, content_type="application/json")


class TimeEventView(View):
    """Class representing a single time_event resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        time_event_id = self.request.match_info["time_eventId"]
        logging.debug(f"Got get request for time_event {time_event_id}")

        try:
            time_event = await TimeEventsService.get_time_event_by_id(db, time_event_id)
        except TimeEventNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        logging.debug(f"Got time_event: {time_event}")
        body = time_event.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(
                token, roles=["admin", "event-admin", "race-result"]
            )
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
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except TimeEventNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete time-event and also remove from race-result function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(
                token, roles=["admin", "event-admin", "race-result"]
            )
        except Exception as e:
            raise e from e

        time_event_id = self.request.match_info["time_eventId"]
        logging.debug(f"Got delete request for time_event {time_event_id}")

        try:
            time_event: TimeEvent = await TimeEventsService.get_time_event_by_id(
                db, time_event_id
            )
            # First we try to remove time-event from race-result's ranking-sequence:
            if time_event.race_id:
                race_results: List[
                    RaceResult
                ] = await RaceResultsService.get_race_results_by_race_id_and_timing_point(
                    db, time_event.race_id, time_event.timing_point
                )
                for race_result in race_results:
                    # We try to remove time-event and subtract counter:
                    try:
                        race_result.ranking_sequence.remove(time_event_id)
                        race_result.no_of_contestants -= 1
                        # Update race-result:
                        await RaceResultsService.update_race_result(
                            db, race_result.id, race_result
                        )
                    except ValueError:  # pragma: no cover
                        pass  # We do not care if it is not there
            # We are ready to remove the time-event
            await TimeEventsService.delete_time_event(db, time_event_id)
        except TimeEventNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
