"""Resource module for startlists resources."""

import json
import logging
import os
from typing import TYPE_CHECKING

from aiohttp.web import (
    HTTPNotFound,
    Response,
    View,
)
from dotenv import load_dotenv

from race_service.adapters import (
    RacesAdapter,
    StartEntriesAdapter,
    StartlistNotFoundError,
    StartlistsAdapter,
    UsersAdapter,
)
from race_service.services import (
    RacesService,
    StartEntriesService,
    StartlistsService,
)
from race_service.utils.jwt_utils import extract_token_from_request

if TYPE_CHECKING: # pragma: no cover
    from race_service.models import StartEntry, Startlist
    from race_service.models.race_model import IndividualSprintRace, IntervalStartRace

load_dotenv()

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class StartlistsView(View):
    """Class representing startlists resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        if "eventId" in self.request.rel_url.query:
            event_id = self.request.rel_url.query["eventId"]
            startlists = await StartlistsAdapter.get_startlists_by_event_id(
                db, event_id
            )
            for startlist in startlists:
                start_entries: list[StartEntry] = []
                for start_entry_id in startlist.start_entries:
                    start_entry = await StartEntriesAdapter.get_start_entry_by_id(
                        db, start_entry_id
                    )
                    if "bib" in self.request.rel_url.query:
                        if start_entry.bib == int(self.request.rel_url.query["bib"]):
                            start_entries.append(start_entry)
                    else:
                        start_entries.append(start_entry)
                startlist.start_entries = start_entries  # type: ignore [reportAttributeAccessIssue]

        else:
            startlists = await StartlistsAdapter.get_all_startlists(db)

        _startlists = [startlist.to_dict() for startlist in startlists]

        body = json.dumps(_startlists, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")


class StartlistView(View):
    """Class representing a single startlist resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        startlist_id = self.request.match_info["startlistId"]
        logging.debug(f"Got get request for startlist {startlist_id}")

        try:
            startlist: Startlist = await StartlistsAdapter.get_startlist_by_id(
                db, startlist_id
            )
            start_entries: list[StartEntry] = []
            for start_entry_id in startlist.start_entries:
                start_entry = await StartEntriesAdapter.get_start_entry_by_id(
                    db, start_entry_id
                )
                start_entries.append(start_entry)
            startlist.start_entries = start_entries  # type: ignore [reportAttributeAccessIssue]
        except StartlistNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        logging.debug(f"Got startlist: {startlist}")
        body = startlist.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def delete(self) -> Response:
        """Delete startlist, and start-entries in it."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "event-admin"])
        except Exception as e:
            raise e from e

        startlist_id = self.request.match_info["startlistId"]
        logging.debug(f"Got delete request for startlist {startlist_id}")

        try:
            startlist_to_be_deleted: Startlist = (
                await StartlistsAdapter.get_startlist_by_id(db, startlist_id)
            )

            # First we need to remove all the start-entries:
            for start_entry_id in startlist_to_be_deleted.start_entries:
                await StartEntriesService.delete_start_entry(db, start_entry_id)

            # We also need to remove all start-entries in the event's races:
            races = await RacesAdapter.get_races_by_event_id(
                db, startlist_to_be_deleted.event_id
            )
            race: IndividualSprintRace | IntervalStartRace
            for race in races:
                race.start_entries = []
                await RacesService.update_race(db, race.id, race)

            # We can then delete the startlist:
            await StartlistsService.delete_startlist(db, startlist_id)
        except StartlistNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
