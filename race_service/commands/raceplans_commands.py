"""Module for raceplan commands."""
from datetime import date, time
from typing import Any, Dict, List, Union

from race_service.adapters import (
    CompetitionFormatNotFoundException,
    EventNotFoundException,
    EventsAdapter,
    RaceclassesNotFoundException,
    RaceplansAdapter,
    RacesAdapter,
)
from race_service.models import IndividualSprintRace, IntervalStartRace, Raceplan
from race_service.services import (
    RaceplanAllreadyExistException,
    RaceplansService,
    RacesService,
)
from .exceptions import (
    CompetitionFormatNotSupportedException,
    CouldNotCreateRaceException,
    CouldNotCreateRaceplanException,
    InconsistentValuesInRaceclassesException,
    InvalidDateFormatException,
    MissingPropertyException,
    NoRaceclassesInEventException,
)
from .raceplans_individual_sprint import calculate_raceplan_individual_sprint
from .raceplans_interval_start import calculate_raceplan_interval_start


class RaceplansCommands:
    """Class representing a commands on events."""

    @classmethod
    async def generate_raceplan_for_event(  # noqa: C901
        cls: Any, db: Any, token: str, event_id: str
    ) -> str:
        """Generate raceplan for event function."""
        # First we check if event already has a plan:
        try:
            await get_raceplan(db, token, event_id)
        except RaceplanAllreadyExistException as e:
            raise e from e
        # First we get the event from the event-service:
        try:
            event = await get_event(token, event_id)
        except EventNotFoundException as e:
            raise e from e
        # We fetch the competition-format:
        try:
            competition_format = await get_competition_format(
                token, event_id, event["competition_format"]
            )
        except CompetitionFormatNotFoundException as e:
            raise CompetitionFormatNotSupportedException(
                f'Competition-format {event["competition_format"]} is not supported.'
            ) from e
        # Then we fetch the raceclasses:
        try:
            raceclasses = await get_raceclasses(token, event_id)
        except NoRaceclassesInEventException as e:
            raise e from e

        # Calculate the raceplan:
        if event["competition_format"] == "Individual Sprint":
            raceplan, races = await calculate_raceplan_individual_sprint(
                event, competition_format, raceclasses
            )
        elif event["competition_format"] == "Interval Start":
            raceplan, races = await calculate_raceplan_interval_start(  # type: ignore
                event, competition_format, raceclasses
            )
        else:
            raise CompetitionFormatNotSupportedException(
                f'Competition-format "{event["competition_format"]!r}" not supported.'
            )
        # Finally we store the races and the raceplan and return the id to the plan:
        raceplan_id = await RaceplansService.create_raceplan(db, raceplan)
        if raceplan_id:
            for race in races:
                race.raceplan_id = raceplan_id
                race_id = await RacesService.create_race(db, race)
                if race_id:
                    raceplan.races.append(race_id)
                else:
                    raise CouldNotCreateRaceException(
                        "Something went wrong when creating race."
                    ) from None
            await RaceplansService.update_raceplan(db, raceplan_id, raceplan)
            return raceplan_id
        raise CouldNotCreateRaceplanException(
            "Something went wrong when creating raceplan."
        ) from None

    @classmethod
    async def validate_raceplan(  # noqa: C901
        cls: Any, db: Any, token: str, raceplan: Raceplan
    ) -> Dict[int, List[str]]:
        """Validate a given raceplan and return validation results."""
        # First we get the event from the event-service:
        try:
            event = await get_event(token, raceplan.event_id)
        except EventNotFoundException as e:  # pragma: no cover
            raise e from e
        # We fetch the competition-format:
        try:
            competition_format = await get_competition_format(
                token, raceplan.event_id, event["competition_format"]
            )
        except CompetitionFormatNotFoundException as e:  # pragma: no cover
            raise CompetitionFormatNotSupportedException(
                f'Competition-format {event["competition_format"]} is not supported.'
            ) from e
        # Then we fetch the raceclasses:
        try:
            raceclasses = await get_raceclasses(token, raceplan.event_id)
        except NoRaceclassesInEventException as e:  # pragma: no cover
            raise e from e

        results: Dict[int, List[str]] = {}

        races: List[Union[IndividualSprintRace, IntervalStartRace]] = []
        for race_id in raceplan.races:
            race = await RacesAdapter.get_race_by_id(db, race_id)
            races.append(race)

        races.sort(key=lambda x: x.order)

        # Check if races are in chronological order:
        for i in range(0, len(races) - 1):
            if races[i].start_time >= races[i + 1].start_time:
                results[races[i + 1].order] = [
                    "Start time is not in chronological order."
                ]

        # Check each race and sum up the number of contestants:
        sum_no_of_contestants = 0
        for race in races:
            # Check if race has contestants:
            if race.no_of_contestants == 0:
                if race.order in results:
                    results[race.order].append("Race has no contestants.")
                else:
                    results[race.order] = [("Race has no contestants.")]

            # Sum up the number of contestants in races:
            if isinstance(race, IndividualSprintRace):
                if race.round in [  # type: ignore
                    competition_format["rounds_ranked_classes"][0],
                    competition_format["rounds_non_ranked_classes"][0],
                ]:
                    sum_no_of_contestants += race.no_of_contestants
            else:
                sum_no_of_contestants += race.no_of_contestants

        # Check if the sum of contestants in races is equal to the number of contestants in the raceplan:
        if sum_no_of_contestants != raceplan.no_of_contestants:
            results[0] = [
                f"The sum of contestants in races ({sum_no_of_contestants})"
                f" is not equal to the number of contestants in the raceplan ({raceplan.no_of_contestants})."
            ]

        # Check if the number of contestants in the plan is equal to
        # the number of contestants in the raceclasses:
        no_of_contestants_in_raceclasses = sum(
            raceclass["no_of_contestants"] for raceclass in raceclasses
        )
        if raceplan.no_of_contestants != no_of_contestants_in_raceclasses:
            if 0 in results:
                results[0].append(
                    (
                        f"Number of contestants in raceplan ({raceplan.no_of_contestants})"
                        " is not equal to the number of contestants"
                        f" in the raceclasses ({no_of_contestants_in_raceclasses})."
                    )
                )
            else:  # pragma: no cover
                results[0] = [
                    (
                        f"Number of contestants in raceplan ({raceplan.no_of_contestants})"
                        f" is not equal to the number of contestants"
                        f" in the raceclasses ({no_of_contestants_in_raceclasses})."
                    )
                ]

        return results


# helpers
async def get_raceplan(db: Any, token: str, event_id: str) -> None:
    """Check if the event already has a raceplan."""
    existing_rp = await RaceplansAdapter.get_raceplans_by_event_id(db, event_id)
    if existing_rp:
        raise RaceplanAllreadyExistException(
            f'Event "{event_id!r}" already has a raceplan.'
        )


async def get_event(token: str, event_id: str) -> dict:
    """Get the event and validate."""
    try:
        event = await EventsAdapter.get_event_by_id(token, event_id)
    except EventNotFoundException as e:
        raise e from e
    # Check if the event has a competition-format:
    if "competition_format" not in event:
        raise CompetitionFormatNotSupportedException(
            f"Event {event_id} has no value for competition_format."
        ) from None

    # We check if event has valid date:
    if "date_of_event" in event:
        await check_date(event["date_of_event"])
    else:
        raise MissingPropertyException(
            'Event does not have a value for "date_of_event".'
        ) from None

    if "time_of_event" in event:
        await check_time(event["time_of_event"])
    else:
        raise MissingPropertyException(
            'Event does not have a value for "time_of_event".'
        ) from None

    return event


async def check_date(date_str: str) -> None:
    """Validate date from string."""
    try:
        date.fromisoformat(date_str)
    except ValueError as e:
        raise InvalidDateFormatException(
            f'Date "{date_str!r}" has invalid format".'
        ) from e


async def check_time(time_str: str) -> None:
    """Validate time from string."""
    try:
        time.fromisoformat(time_str)
    except ValueError as e:
        raise InvalidDateFormatException('Time "{time_str}" has invalid format.') from e


async def get_competition_format(
    token: str, event_id: str, competition_format_name: str
) -> dict:
    """Get the competition-format."""
    try:
        competition_format = await EventsAdapter.get_competition_format(
            token, event_id, competition_format_name
        )
    except CompetitionFormatNotFoundException as e:
        raise e from e
    # Validate:
    if "max_no_of_contestants_in_raceclass" not in competition_format:
        raise MissingPropertyException(
            f'Competition format "{competition_format_name!r}" '
            'is missing the "max_no_of_contestants_in_raceclass" property.'
        )

    if "max_no_of_contestants_in_race" not in competition_format:
        raise MissingPropertyException(
            f'Competition format "{competition_format_name!r}" '
            'is missing the "max_no_of_contestants_in_race" property.'
        )

    if competition_format["name"] == "Interval Start":
        if "intervals" not in competition_format:
            raise MissingPropertyException(
                f'Competition format "{competition_format_name!r}" '
                'is missing the "intervals" property.'
            )
        # We do have intervals, check if valid format:
        await check_time(competition_format["intervals"])

    return competition_format


async def get_raceclasses(token: str, event_id: str) -> List[dict]:  # noqa: C901
    """Get the raceclasses."""
    raceclasses = []
    try:
        raceclasses = await EventsAdapter.get_raceclasses(token, event_id)
    except RaceclassesNotFoundException:
        pass
    # Validate:
    # Check if there in fact _are_ raceclasses in the list:
    if len(raceclasses) == 0:
        raise NoRaceclassesInEventException(
            f"No raceclass for event {event_id}. Cannot proceed."
        )

    # Validate `group` property:
    # Check if raceclasses have only integers group values:
    if not all(
        isinstance(o, (int)) for o in [r.get("group", None) for r in raceclasses]
    ):
        raise InconsistentValuesInRaceclassesException(
            f"Raceclasses group values for event {event_id} contains non numeric values."
        )

    # Check if the group values are consecutive:
    if not sorted(set([r["group"] for r in raceclasses])) == list(
        range(
            min(set([r["group"] for r in raceclasses])),
            max(set([r["group"] for r in raceclasses])) + 1,
        )
    ):
        raise InconsistentValuesInRaceclassesException(
            f"Raceclasses group values for event {event_id} are not consecutive."
        )

    # Validate `order` property:
    # Check if raceclasses have only integers order values:
    if not all(
        isinstance(o, (int)) for o in [r.get("order", None) for r in raceclasses]
    ):
        raise InconsistentValuesInRaceclassesException(
            f"Raceclasses order values for event {event_id} contains non numeric values."
        )
    # Check if raceclasses have complete and unique values for `order` pr group:
    # sort the raceclasses on group and order:
    raceclasses_sorted = sorted(raceclasses, key=lambda k: (k["group"], k["order"]))
    # We need to group the raceclasses by group:
    d: Dict[int, list] = {}
    for raceclass in raceclasses_sorted:
        d.setdefault(raceclass["group"], []).append(raceclass)
    raceclasses_grouped = list(d.values())
    for _raceclasses in raceclasses_grouped:
        if len(_raceclasses) != len(set([r["order"] for r in _raceclasses])):
            raise InconsistentValuesInRaceclassesException(
                f"Raceclasses order values for event {event_id} are not unique inside group."
            )

    # Check if the order values are consecutive:
    for _raceclasses in raceclasses_grouped:
        if not sorted([r["order"] for r in _raceclasses]) == list(
            range(
                min([r["order"] for r in _raceclasses]),
                max([r["order"] for r in _raceclasses]) + 1,
            )
        ):
            raise InconsistentValuesInRaceclassesException(
                f"Raceclasses order values for event {event_id} are not consecutive."
            )

    # Ranking-value must be the same for all races in a group:
    for _raceclasses in raceclasses_grouped:
        if len(set([r["ranking"] for r in _raceclasses])) > 1:
            raise InconsistentValuesInRaceclassesException(
                f'Ranking-value differs in group {_raceclasses[0]["group"]}.'
            )
    return raceclasses
