"""Resource module for races resources."""
import json
import logging
import os
from typing import Dict, List

from aiohttp.web import (
    HTTPNotFound,
    HTTPUnprocessableEntity,
    Response,
    View,
)
from dotenv import load_dotenv

from race_service.adapters import UsersAdapter
from race_service.models import (
    Race,
    StartEntry,
    TimeEvent,
)
from race_service.models.race_model import RaceResult
from race_service.services import (
    IllegalValueException,
    RaceNotFoundException,
    RaceResultsService,
    RacesService,
    StartEntriesService,
    TimeEventsService,
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
            # Get the start_entries:
            start_entries: List[StartEntry] = []
            for start_entry_id in race.start_entries:
                start_entry: StartEntry = (
                    await StartEntriesService.get_start_entry_by_id(db, start_entry_id)
                )
                start_entries.append(start_entry)

            # We sort the start_entries on position:
            start_entries_sorted = sorted(
                start_entries,
                key=lambda k: (
                    k.starting_position is not None,
                    k.starting_position != "",
                    k.starting_position,
                ),
                reverse=False,
            )

            race.start_entries = start_entries_sorted  # type: ignore
            # Get the race_results:
            results: Dict[str, RaceResult] = {}
            for key in race.results:
                race_result: RaceResult = (
                    await RaceResultsService.get_race_result_by_id(
                        db, race.results[key]
                    )
                )
                ranking_sequence: List[TimeEvent] = []
                for time_event_id in race_result.ranking_sequence:
                    time_event = await TimeEventsService.get_time_event_by_id(
                        db, time_event_id
                    )
                    ranking_sequence.append(time_event)
                # We sort the time-events on rank:
                ranking_sequence_sorted = sorted(
                    ranking_sequence,
                    key=lambda k: (
                        k.rank is not None,
                        k.rank != "",
                        k.rank,
                    ),
                    reverse=False,
                )

                race_result.ranking_sequence = ranking_sequence_sorted  # type: ignore
                results[key] = race_result
            race.results = results  # type: ignore
        except RaceNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
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
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except RaceNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete the race."""
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
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
