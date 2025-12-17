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
from dotenv import load_dotenv
from multidict import MultiDict

from race_service.adapters import (
    EventsAdapter,
    RaceNotFoundError,
    RaceplansAdapter,
    RacesAdapter,
    StartEntriesAdapter,
    StartEntryNotFoundError,
    StartlistNotFoundError,
    StartlistsAdapter,
    UsersAdapter,
)
from race_service.models import (
    StartEntry,
    Startlist,
)
from race_service.models.race_model import IndividualSprintRace, IntervalStartRace
from race_service.services import (
    CouldNotCreateStartEntryError,
    IllegalValueError,
    RaceplansService,
    RacesService,
    StartEntriesService,
    StartlistsService,
)
from race_service.utils.jwt_utils import extract_token_from_request

load_dotenv()

HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class StartEntriesView(View):
    """Class representing start_entries resource."""

    logger = logging.getLogger("race_service.views.start_entries.StartEntriesView")

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        race_id = self.request.match_info["raceId"]

        if "startlistId" in self.request.rel_url.query:
            startlist_id = self.request.rel_url.query["startlistId"]
            start_entries = (
                await StartEntriesAdapter.get_start_entries_by_race_id_and_startlist_id(
                    db, race_id, startlist_id
                )
            )
        else:
            start_entries = await StartEntriesAdapter.get_start_entries_by_race_id(
                db, race_id
            )

        _start_entries = [start_entry.to_dict() for start_entry in start_entries]

        body = json.dumps(_start_entries, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:
        """Create the start_entry and add it to the race and startlist."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(
                token, roles=["admin", "event-admin", "race-result", "race-office"]
            )
        except Exception as e:
            raise e from e

        body = await self.request.json()
        self.logger.debug(
            f"Got create request for start_entry {body} of type {type(body)}"
        )
        try:
            new_start_entry = StartEntry.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            # First we need to get to the startlist the new start-entry is part of:
            startlist = await StartlistsAdapter.get_startlist_by_id(
                db, new_start_entry.startlist_id
            )
            # We need to check if the bib is already in the race, and
            # if the given starting-position is vacant, or
            # if there open starting-positions:
            race: (
                IndividualSprintRace | IntervalStartRace
            ) = await RacesAdapter.get_race_by_id(db, new_start_entry.race_id)
            start_entries_in_race = (
                await StartEntriesAdapter.get_start_entries_by_race_id(db, race.id)
            )
            bibs_in_race = [start_entry.bib for start_entry in start_entries_in_race]
            starting_positions_in_race = [
                start_entry.starting_position for start_entry in start_entries_in_race
            ]
            if not len(race.start_entries) < race.max_no_of_contestants:
                raise HTTPBadRequest(
                    reason="Cannot add start-entry: race is full."
                ) from None
            if new_start_entry.bib in bibs_in_race:
                raise HTTPBadRequest(
                    reason=f"Cannot add start-entry: Bib {new_start_entry.bib} is already in the race."
                ) from None
            if new_start_entry.starting_position in starting_positions_in_race:
                raise HTTPBadRequest(
                    reason=(
                        "Cannot add start-entry: Starting_position"
                        f"{new_start_entry.starting_position} is taken."
                    )
                ) from None

            # We can create the start-entry:
            start_entry_id = await StartEntriesService.create_start_entry(
                db, new_start_entry
            )

            # We need to add the start-entry to the race:
            race.start_entries.append(start_entry_id)
            race.no_of_contestants = len(race.start_entries)
            await RacesService.update_race(db, race.id, race)

            # If the race is in first round, we need to add to the raceplan's no_of_contestants:
            competition_format = await EventsAdapter.get_competition_format(
                token=token,  # type: ignore [reportArgumentType]
                event_id=race.event_id,
            )
            first_rounds = [
                competition_format["rounds_ranked_classes"][0],
                competition_format["rounds_non_ranked_classes"][0],
            ]
            if isinstance(race, IndividualSprintRace) and race.round in first_rounds:
                raceplan = await RaceplansAdapter.get_raceplan_by_id(
                    db, race.raceplan_id
                )
                raceplan.no_of_contestants += 1
                await RaceplansService.update_raceplan(db, raceplan.id, raceplan)  # type: ignore [reportArgumentType]

            # We also need to add the start-entry to the startlist
            # and add the start_entry to it's no_of_contestants
            startlist.no_of_contestants += 1
            startlist.start_entries.append(start_entry_id)
            assert startlist.id  # noqa: S101
            await StartlistsService.update_startlist(db, startlist.id, startlist)
        except IllegalValueError as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except (
            StartlistNotFoundError,
            RaceNotFoundError,
            CouldNotCreateStartEntryError,
        ) as e:
            raise HTTPBadRequest(reason=str(e)) from e
        self.logger.debug(f"inserted document with start_entry_id {start_entry_id}")

        headers = MultiDict(
            [
                (
                    hdrs.LOCATION,
                    f"{BASE_URL}/races/{race.id}/start-entries/{start_entry_id}",
                )
            ]
        )

        return Response(status=201, headers=headers)


class StartEntryView(View):
    """Class representing a single start_entry resource."""

    logger = logging.getLogger("race_service.views.start_entries.StartEntryView")

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]

        start_entry_id = self.request.match_info["startEntryId"]
        self.logger.debug(f"Got get request for start_entry {start_entry_id}")

        try:
            start_entry = await StartEntriesAdapter.get_start_entry_by_id(
                db, start_entry_id
            )
        except StartEntryNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        self.logger.debug(f"Got start_entry: {start_entry}")
        body = start_entry.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(
                token, roles=["admin", "event-admin", "race-result", "race-office"]
            )
        except Exception as e:
            raise e from e

        body = await self.request.json()
        start_entry_id = self.request.match_info["startEntryId"]
        self.logger.debug(
            f"Got request-body {body} for {start_entry_id} of type {type(body)}"
        )
        body = await self.request.json()
        self.logger.debug(
            f"Got put request for start_entry {body} of type {type(body)}"
        )
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
        except IllegalValueError as e:
            raise HTTPUnprocessableEntity(reason=str(e)) from e
        except StartEntryNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete the start-entry."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(
                token, roles=["admin", "event-admin", "race-result", "race-office"]
            )
        except Exception as e:
            raise e from e

        start_entry_for_deletion_id = self.request.match_info["startEntryId"]
        self.logger.debug(
            f"Got delete request for start_entry {start_entry_for_deletion_id}"
        )

        try:
            start_entry: StartEntry = await StartEntriesAdapter.get_start_entry_by_id(
                db, start_entry_for_deletion_id
            )
            # We need to remove the start-entry from the race containing the start-entry:
            try:
                race: (
                    IndividualSprintRace | IntervalStartRace
                ) = await RacesAdapter.get_race_by_id(db, start_entry.race_id)
            except RaceNotFoundError as e:
                raise HTTPNotFound(
                    reason=(
                        f"DB is inconsistent: cannot find race with id "
                        f"{start_entry.race_id} of start-entry with id {start_entry.id}"
                    )
                ) from e
            # Remove the start-entry from races start-entries
            new_start_entries = [
                start_entry_id
                for start_entry_id in race.start_entries
                if start_entry_id != start_entry_for_deletion_id
            ]
            race.start_entries = new_start_entries
            race.no_of_contestants = len(race.start_entries)
            await RacesService.update_race(db, race.id, race)

            # If the race is in first round, we need to subract from the raceplan's no_of_contestants:
            competition_format = await EventsAdapter.get_competition_format(
                token=token,  # type: ignore [reportArgumentType]
                event_id=race.event_id,
            )
            first_rounds = [
                competition_format["rounds_ranked_classes"][0],
                competition_format["rounds_non_ranked_classes"][0],
            ]
            if isinstance(race, IndividualSprintRace) and race.round in first_rounds:
                raceplan = await RaceplansAdapter.get_raceplan_by_id(
                    db, race.raceplan_id
                )
                raceplan.no_of_contestants -= 1
                await RaceplansService.update_raceplan(db, raceplan.id, raceplan)  # type: ignore [reportArgumentType]

            # We also need to remove the start-entry from the startlist,
            # and subtract the start_entry from it's no_of_contestants
            try:
                startlist: Startlist = await StartlistsAdapter.get_startlist_by_id(
                    db, start_entry.startlist_id
                )
            except StartlistNotFoundError as e:
                raise HTTPNotFound(
                    reason=(
                        f"DB is inconsistent: cannot find startlist with id "
                        f"{start_entry.startlist_id} of start-entry with id {start_entry.id}"
                    )
                ) from e
            new_start_entries = [
                start_entry_id
                for start_entry_id in startlist.start_entries
                if start_entry_id != start_entry_for_deletion_id
            ]
            startlist.start_entries = new_start_entries
            startlist.no_of_contestants += -1
            await StartlistsService.update_startlist(db, startlist.id, startlist)  # type: ignore [reportArgumentType]

            # We can finally delete the start-entry:
            await StartEntriesService.delete_start_entry(
                db, start_entry_for_deletion_id
            )
        except StartEntryNotFoundError as e:
            raise HTTPNotFound(reason=str(e)) from e
        return Response(status=204)
