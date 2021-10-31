"""Resource module for raceplans resources."""
import json
import logging
import os
from typing import List, Union

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
from race_service.models import IndividualSprintRace, IntervalStartRace, Raceplan
from race_service.services import (
    IllegalValueException,
    RaceNotFoundException,
    RaceplanAllreadyExistException,
    RaceplanNotFoundException,
    RaceplansService,
    RacesService,
)
from .utils import extract_token_from_request

load_dotenv()
HOST_SERVER = os.getenv("HOST_SERVER", "localhost")
HOST_PORT = os.getenv("HOST_PORT", "8080")
BASE_URL = f"http://{HOST_SERVER}:{HOST_PORT}"


class RaceplansView(View):
    """Class representing raceplans resource."""

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
            raceplans = await RaceplansService.get_raceplan_by_event_id(db, event_id)
        else:
            raceplans = await RaceplansService.get_all_raceplans(db)
        list = []
        for _e in raceplans:
            list.append(_e.to_dict())

        body = json.dumps(list, default=str, ensure_ascii=False)
        return Response(status=200, body=body, content_type="application/json")

    async def post(self) -> Response:  # noqa: C901
        """Create the raceplan and all the races in it."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        logging.debug(f"Got create request for raceplan {body} of type {type(body)}")
        try:
            raceplan = Raceplan.from_dict(body)
            raceplan.races = []  # We add the races later.
            races: List[Union[IndividualSprintRace, IntervalStartRace]] = []
            for race in body["races"]:
                race["id"] = ""
                if "event_id" not in race:
                    race["event_id"] = raceplan.event_id
                if "raceplan_id" not in race:
                    race["raceplan_id"] = ""
                if "startlist_id" not in race:
                    race["startlist_id"] = ""

                if race["datatype"] == "individual_sprint":
                    races.append(IndividualSprintRace.from_dict(race))
                elif race["datatype"] == "interval_start":
                    races.append(IntervalStartRace.from_dict(race))
                else:
                    raise HTTPBadRequest(
                        reason=f'Race of type "{race["datatype"]}" not supported.'
                    )
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            # Finally we store the races and the raceplan and return the id to the plan:
            raceplan_id = await RaceplansService.create_raceplan(db, raceplan)
            if raceplan_id:
                for race in races:
                    race.raceplan_id = raceplan_id
                    race_id = await RacesService.create_race(db, race)
                    if race_id:
                        raceplan.races.append(race_id)
                await RaceplansService.update_raceplan(db, raceplan_id, raceplan)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        except RaceplanAllreadyExistException as e:
            raise HTTPBadRequest(reason=e) from e
        if raceplan_id:
            logging.debug(f"inserted document with raceplan_id {raceplan_id}")
            headers = MultiDict({hdrs.LOCATION: f"{BASE_URL}/raceplans/{raceplan_id}"})

            return Response(status=201, headers=headers)
        raise HTTPBadRequest() from None


class RaceplanView(View):
    """Class representing a single raceplan resource."""

    async def get(self) -> Response:
        """Get route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        raceplan_id = self.request.match_info["raceplanId"]
        logging.debug(f"Got get request for raceplan {raceplan_id}")

        try:
            raceplan = await RaceplansService.get_raceplan_by_id(db, raceplan_id)
            races: List[Union[IndividualSprintRace, IntervalStartRace]] = []
            # Replace list of race-ids with corresponding races:
            for race_id in raceplan.races:
                race = await RacesService.get_race_by_id(db, race_id)
                races.append(race)
            raceplan.races = races  # type: ignore
        except RaceplanNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        logging.debug(f"Got raceplan: {raceplan}")
        body = raceplan.to_json()
        return Response(status=200, body=body, content_type="application/json")

    async def put(self) -> Response:
        """Put route function."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        body = await self.request.json()
        raceplan_id = self.request.match_info["raceplanId"]
        logging.debug(f"Got request-body {body} for {raceplan_id} of type {type(body)}")
        body = await self.request.json()
        logging.debug(f"Got put request for raceplan {body} of type {type(body)}")
        try:
            raceplan = Raceplan.from_dict(body)
        except KeyError as e:
            raise HTTPUnprocessableEntity(
                reason=f"Mandatory property {e.args[0]} is missing."
            ) from e

        try:
            await RaceplansService.update_raceplan(db, raceplan_id, raceplan)
        except IllegalValueException as e:
            raise HTTPUnprocessableEntity(reason=e) from e
        except RaceplanNotFoundException as e:
            raise HTTPNotFound(reason=e) from e
        return Response(status=204)

    async def delete(self) -> Response:
        """Delete the reaceplan and all the races in it."""
        db = self.request.app["db"]
        token = extract_token_from_request(self.request)
        try:
            await UsersAdapter.authorize(token, roles=["admin", "raceplan-admin"])
        except Exception as e:
            raise e from e

        raceplan_id = self.request.match_info["raceplanId"]
        logging.debug(f"Got delete request for raceplan {raceplan_id}")

        try:
            raceplan = await RaceplansService.get_raceplan_by_id(db, raceplan_id)
            for race_id in raceplan.races:
                await RacesService.delete_race(db, race_id)
            await RaceplansService.delete_raceplan(db, raceplan_id)
        except (RaceplanNotFoundException, RaceNotFoundException) as e:
            raise HTTPNotFound(reason=e) from e
        return Response(status=204)
