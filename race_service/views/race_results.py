"""Resource module for race_results resources."""
import json
import logging
import os
from typing import List, Union

from aiohttp.web import (
    HTTPNotFound,
    HTTPUnprocessableEntity,
    Response,
    View,
)
from aiohttp.web_exceptions import HTTPInternalServerError
from dotenv import load_dotenv

from race_service.adapters import UsersAdapter
from race_service.models import (
    IndividualSprintRace,
    IntervalStartRace,
    RaceResult,
    TimeEvent,
)
from race_service.services import (
    IllegalValueException,
    RaceNotFoundException,
    RaceResultNotFoundException,
    RaceResultsService,
    RacesService,
    TimeEventsService,
)
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class RaceResultsView(View):
    """Class representing race_results resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "race-result-admin"])
        except Exception as e:
            raise e from e

        race_id = self.request.match_info["raceId"]

        if "timingPoint" in self.request.rel_url.query:
            timing_point = self.request.rel_url.query["timingPoint"]
            race_results = (
                await RaceResultsService.get_race_results_by_race_id_and_timing_point(
                    db, race_id, timing_point
                )
            )
        else:
            race_results = await RaceResultsService.get_race_results_by_race_id(
                db, race_id
            )
        # We expand references to time-events in race-results ranking-sequence:
        for race_result in race_results:
            time_events: List[TimeEvent] = []
            time_events_sorted: List[TimeEvent] = []
            for time_event_id in race_result.ranking_sequence:
                time_event = await TimeEventsService.get_time_event_by_id(
                    db, time_event_id
                )
                time_events.append(time_event)
                # We sort the time-events on rank:
                time_events_sorted = sorted(
                    time_events,
                    key=lambda k: (
                        k.rank is not None,
                        k.rank != "",
                        k.rank,
                    ),
                    reverse=False,
                )

            race_result.ranking_sequence = time_events_sorted  # type: ignore

        list = []
        for race_result in race_results:
            list.append(race_result.to_dict())

        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")


class RaceResultView(View):
    """Class representing a single race_result resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "race-result-admin"])
        except Exception as e:
            raise e from e

        race_result_id = self.request.match_info["raceResultId"]
        logging.debug(f"Got get request for race_result {race_result_id}")

        try:
            race_result = await RaceResultsService.get_race_result_by_id(
                db, race_result_id
            )
            # We expand references to time-events in race-result's ranking-sequence:
            time_events: List[TimeEvent] = []
            for time_event_id in race_result.ranking_sequence:
                time_event = await TimeEventsService.get_time_event_by_id(
                    db, time_event_id
                )
                time_events.append(time_event)
                # We sort the time-events on rank:
                time_events_sorted = sorted(
                    time_events,
                    key=lambda k: (
                        k.rank is not None,
                        k.rank != "",
                        k.rank,
                    ),
                    reverse=False,
                )

            race_result.ranking_sequence = time_events_sorted  # type: ignore
        except RaceResultNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        logging.debug(f"Got race_result: {race_result}")
        body = race_result.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "race-result-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        race_result_id = self.request.match_info["raceResultId"]
        logging.debug(
            f"Got request-body {body} for {race_result_id} of type {type(body)}"
        )
        body = await self.request.json()
        logging.debug(f"Got put request for race_result {body} of type {type(body)}")
        try:
            race_result = RaceResult.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await RaceResultsService.update_race_result(db, race_result_id, race_result)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except RaceResultNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete the race-result and all the race_results in it."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "race-result-admin"])
        except Exception as e:
            raise e from e

        race_result_for_deletion_id = self.request.match_info["raceResultId"]
        logging.debug(
            f"Got delete request for race_result {race_result_for_deletion_id}"
        )

        try:
            race_result: RaceResult = await RaceResultsService.get_race_result_by_id(
                db, race_result_for_deletion_id
            )
            # We need to remove the race-result from the race containing the race-result:
            try:
                race: Union[
                    IndividualSprintRace, IntervalStartRace
                ] = await RacesService.get_race_by_id(db, race_result.race_id)
            except RaceNotFoundException as e:
                raise HTTPInternalServerError(
                    reason=(
                        f"DB is inconsistent: cannot find race with id "
                        f"{race_result.race_id} of race-result with id {race_result.id}"
                    )
                ) from e
            del race.results[race_result.timing_point]
            await RacesService.update_race(db, race.id, race)

            # We can finally delete the race-result:
            await RaceResultsService.delete_race_result(db, race_result_for_deletion_id)
        except RaceResultNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
