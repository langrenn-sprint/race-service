"""Resource module for races resources."""
import json
import logging
import os
from typing import Any, Dict, List, Union

from aiohttp.web import (
    HTTPNotFound,
    HTTPUnprocessableEntity,
    Response,
    View,
)
from dotenv import load_dotenv

from race_service.adapters import UsersAdapter
from race_service.models import (
    StartEntry,
    TimeEvent,
)
from race_service.models.race_model import (
    IndividualSprintRace,
    IntervalStartRace,
    RaceResult,
)
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

        if "eventId" in self.request.rel_url.query:
            event_id = self.request.rel_url.query["eventId"]
            if "raceclass" in self.request.rel_url.query:
                raceclass = self.request.rel_url.query["raceclass"]
                races = await RacesService.get_races_by_event_id_and_raceclass(
                    db, event_id, raceclass
                )
                if races:
                    for race in races:
                        # Get the start_entries:
                        race.start_entries = await get_start_entries(db, race.start_entries)  # type: ignore
                        # Get the race_results:
                        race.results = await get_race_results(db, race.results)  # type: ignore
            else:
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

        race_id = self.request.match_info["raceId"]
        logging.debug(f"Got get request for race {race_id}")

        try:
            race = await RacesService.get_race_by_id(db, race_id)
            # Get the start_entries:
            race.start_entries = await get_start_entries(db, race.start_entries)  # type: ignore
            # Get the race_results:
            race.results = await get_race_results(db, race.results)  # type: ignore
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
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        race_id = self.request.match_info["raceId"]
        logging.debug(f"Got request-body {body} for {race_id} of type {type(body)}")
        body = await self.request.json()
        logging.debug(f"Got put request for race {body} of type {type(body)}")
        race: Union[IndividualSprintRace, IntervalStartRace]
        try:
            if body["datatype"] == "individual_sprint":
                race = IndividualSprintRace.from_dict(body)
            elif body["datatype"] == "interval_start":
                race = IntervalStartRace.from_dict(body)
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
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        race_id = self.request.match_info["raceId"]
        logging.debug(f"Got delete request for race {race_id}")

        try:
            await RacesService.delete_race(db, race_id)
        except RaceNotFoundException as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)


async def get_start_entries(db: Any, start_entry_ids: list) -> List[StartEntry]:
    """Get the start entries."""
    start_entries: List[StartEntry] = []
    for start_entry_id in start_entry_ids:
        start_entry: StartEntry = await StartEntriesService.get_start_entry_by_id(
            db, start_entry_id
        )
        start_entries.append(start_entry)

    # We sort the start-entries on starting_position:
    start_entries.sort(
        key=lambda k: (k.starting_position,),
        reverse=False,
    )

    return start_entries


async def get_race_results(db: Any, race_results: dict) -> Dict[str, RaceResult]:
    """Get the race results in sorted order."""
    results: Dict[str, RaceResult] = {}
    for key in race_results:
        if key.lower() != "Template".lower():  # We skip the template
            race_result: RaceResult = await RaceResultsService.get_race_result_by_id(
                db, race_results[key]
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
    return results
