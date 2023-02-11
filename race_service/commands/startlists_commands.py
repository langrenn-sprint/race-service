"""Module for startlist commands."""
from datetime import date, time, timedelta
from typing import Any, Dict, List, Tuple, Union

from race_service.adapters import (
    CompetitionFormatNotFoundException,
    ContestantsNotFoundException,
    EventNotFoundException,
    EventsAdapter,
    RaceclassesNotFoundException,
    RaceplansAdapter,
    RacesAdapter,
    StartlistsAdapter,
)
from race_service.models import (
    IndividualSprintRace,
    IntervalStartRace,
    Raceplan,
    StartEntry,
    Startlist,
)
from race_service.services import (
    RacesService,
    StartEntriesService,
    StartlistAllreadyExistException,
    StartlistsService,
)
from .exceptions import (
    CompetitionFormatNotSupportedException,
    DuplicateRaceplansInEventException,
    InconsistentInputDataException,
    InconsistentValuesInContestantsException,
    InvalidDateFormatException,
    MissingPropertyException,
    NoRaceplanInEventException,
    NoRacesInRaceplanException,
)


class StartlistsCommands:
    """Class representing a commands on events."""

    @classmethod
    async def generate_startlist_for_event(  # noqa: C901
        cls: Any, db: Any, token: str, event_id: str
    ) -> str:
        """Generate startlist for event function."""
        # First we check if event already has a plan:
        try:
            await get_startlist(db, token, event_id)
        except StartlistAllreadyExistException as e:
            raise e from e
        # Then we get the event from the event-service:
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
        raceclasses = await get_raceclasses(token, event_id)
        # Then we fetch the raceplan:
        raceplan = await get_raceplan(db, token, event_id)
        # and the races:
        if raceplan.id:
            races = await get_races(db, token, raceplan.id)
        # And finally we get the list of contestants:
        contestants = await get_contestants(token, event_id)

        # Sanity check:
        no_of_contestants_in_raceclasses = sum(
            raceclass["no_of_contestants"] for raceclass in raceclasses
        )
        if len(contestants) != no_of_contestants_in_raceclasses:
            raise InconsistentInputDataException(
                "len(contestants) does not match number of contestants in raceclasses:"
                f"{len(contestants)} != {no_of_contestants_in_raceclasses}."
            )
        #
        if len(contestants) != raceplan.no_of_contestants:
            raise InconsistentInputDataException(
                "len(contestants) does not match number of contestants in raceplan:"
                f"{len(contestants)} != {raceplan.no_of_contestants}."
            )

        # We are ready to generate the startlist:
        if event["competition_format"] == "Individual Sprint":
            startlist, start_entries = await generate_startlist_for_individual_sprint(
                event,
                competition_format,
                raceclasses,
                raceplan,
                races,  # type: ignore
                contestants,
            )
        elif event["competition_format"] == "Interval Start":
            startlist, start_entries = await generate_startlist_for_interval_start(
                event,
                competition_format,
                raceclasses,
                raceplan,
                races,  # type: ignore
                contestants,
            )
        else:
            raise CompetitionFormatNotSupportedException(
                f'Competition-format "{event["competition_format"]!r}" not supported.'
            )
        # Finally we store the new startlist and return the id:
        startlist_id = await StartlistsService.create_startlist(db, startlist)
        # We create each start_entry:
        for start_entry in start_entries:
            start_entry.startlist_id = startlist_id
            start_entry_id = await StartEntriesService.create_start_entry(
                db, start_entry
            )
            startlist.start_entries.append(start_entry_id)

            # We add the start-entry to the respective race:
            race = await RacesAdapter.get_race_by_id(db, start_entry.race_id)
            race.start_entries.append(start_entry_id)
            await RacesService.update_race(db, race.id, race)
        await StartlistsService.update_startlist(db, startlist_id, startlist)

        return startlist_id


async def generate_startlist_for_individual_sprint(  # noqa: C901
    event: dict,
    competition_format: dict,
    raceclasses: List[dict],
    raceplan: Raceplan,
    races: List[IndividualSprintRace],
    contestants: List[dict],
) -> Tuple[Startlist, List[StartEntry]]:
    """Generate a startlist for an individual sprint event."""
    no_of_contestants = len(contestants)
    start_entries: List[StartEntry] = []
    startlist = Startlist(
        event_id=event["id"],
        no_of_contestants=no_of_contestants,
        start_entries=[],
    )
    #
    no_of_contestants_in_races = sum(
        race.no_of_contestants for race in races if race.round in ["R1", "Q"]
    )
    if len(contestants) != no_of_contestants_in_races:
        raise InconsistentInputDataException(
            "Number of contestants in event does not match sum of contestants in races:"
            f"{len(contestants)} != {no_of_contestants_in_races}."
        )

    #
    # For every race in rounds=Q, R1 or R2 in raceplan grouped by raceclass,
    # get the corresponding ageclasses from raceclass,
    # pick all contestants in ageclasses,
    # and for every such contestant, generate a start_entry.
    # until race is full.

    # First we need to group the races by raceclass:
    d: Dict[str, list] = {}
    for race in races:
        d.setdefault(race.raceclass, []).append(race)
    races_grouped_by_raceclass = list(d.values())

    for races in races_grouped_by_raceclass:
        # We find the actual ageclasses in this raceclass:
        ageclasses: List[str] = []
        ranking = False
        for raceclass in raceclasses:
            if raceclass["name"] == races[0].raceclass:
                ranking = raceclass["ranking"]
                ageclasses += raceclass["ageclasses"]

        # For every contestant in corresponding ageclasses, create a start_entry in
        # a race until it is full, continue with next race:
        race_index = 0
        starting_position = 1
        no_of_contestants_in_race = 0

        for contestant in [
            contestant
            for contestant in contestants
            if contestant["ageclass"] in ageclasses
        ]:
            # Get the actual relevant races and set up control variables:
            if ranking:
                target_races = [race for race in races if race.round == "Q"]
            else:
                target_races = [
                    race for race in races if race.round in ["R1"]
                ]  # pragma: no cover

            # Create the start-entry:
            start_entry = StartEntry(
                id="",
                startlist_id="",
                race_id=target_races[race_index].id,
                bib=contestant["bib"],
                name=f'{contestant["first_name"]} {contestant["last_name"]}',
                club=contestant["club"],
                starting_position=starting_position,
                scheduled_start_time=target_races[race_index].start_time,
            )
            start_entries.append(start_entry)

            no_of_contestants_in_race += 1
            # Check if race is full:
            if no_of_contestants_in_race < target_races[race_index].no_of_contestants:
                starting_position += 1
            else:
                race_index += 1
                starting_position = 1
                no_of_contestants_in_race = 0

        # For not ranked ageclasses we generate round 2 ("R2") also:
        race_index = 0
        starting_position = 1
        no_of_contestants_in_race = 0
        if not ranking:  # pragma: no cover
            for contestant in [
                contestant
                for contestant in contestants
                if contestant["ageclass"] in ageclasses
            ]:
                target_races = [race for race in races if race.round in ["R2"]]

                # Create the start-entry:
                start_entry = StartEntry(
                    id="",
                    startlist_id="",
                    race_id=target_races[race_index].id,
                    bib=contestant["bib"],
                    name=f'{contestant["first_name"]} {contestant["last_name"]}',
                    club=contestant["club"],
                    starting_position=starting_position,
                    scheduled_start_time=target_races[race_index].start_time,
                )
                start_entries.append(start_entry)

                no_of_contestants_in_race += 1
                # Check if race is full:
                if (
                    no_of_contestants_in_race
                    < target_races[race_index].no_of_contestants
                ):
                    starting_position += 1
                else:
                    race_index += 1
                    starting_position = 1
                    no_of_contestants_in_race = 0

    return startlist, start_entries


async def generate_startlist_for_interval_start(
    event: dict,
    competition_format: dict,
    raceclasses: List[dict],
    raceplan: Raceplan,
    races: List[IntervalStartRace],
    contestants: List[dict],
) -> Tuple[Startlist, List[StartEntry]]:
    """Generate a startlist for an interval start event."""
    no_of_contestants = len(contestants)

    no_of_contestants_in_races = sum(race.no_of_contestants for race in races)
    if len(contestants) != no_of_contestants_in_races:
        raise InconsistentInputDataException(
            "len(contestants) does not match sum of contestants in races:"
            f"{len(contestants)} != {no_of_contestants_in_races}."
        )

    start_entries: List[StartEntry] = []
    startlist = Startlist(
        event_id=event["id"],
        no_of_contestants=no_of_contestants,
        start_entries=[],
    )
    interval = timedelta(
        hours=time.fromisoformat(competition_format["intervals"]).hour,
        minutes=time.fromisoformat(competition_format["intervals"]).minute,
        seconds=time.fromisoformat(competition_format["intervals"]).second,
    )
    # For every race in raceplan grouped by raceclass,
    # get the corresponding ageclasses from raceclass,
    # pick all contestants in ageclasses,
    # and for every such contestant, generate a start_entry:

    # First we need to group the races by raceclass:
    d: Dict[str, list] = {}
    for race in races:
        d.setdefault(race.raceclass, []).append(race)
    races_grouped = list(d.values())

    for races in races_grouped:
        for race in races:
            starting_position = 0
            # Get the correponding ageclasses:
            ageclasses: List[str] = []
            for raceclass in raceclasses:
                if raceclass["name"] == race.raceclass:
                    ageclasses += raceclass["ageclasses"]
            # For every contestant in ageclass, create a start_entry:
            scheduled_start_time = race.start_time
            for contestant in [
                contestant
                for contestant in contestants
                if contestant["ageclass"] in ageclasses
            ]:
                bib = contestant["bib"]
                starting_position += 1

                start_entry = StartEntry(
                    id="",
                    startlist_id="",
                    race_id=race.id,
                    bib=bib,
                    name=f'{contestant["first_name"]} {contestant["last_name"]}',
                    club=contestant["club"],
                    starting_position=starting_position,
                    scheduled_start_time=scheduled_start_time,
                )
                scheduled_start_time = scheduled_start_time + interval
                start_entries.append(start_entry)

    return startlist, start_entries


# helpers
async def get_startlist(db: Any, token: str, event_id: str) -> None:
    """Check if the event already has a startlist."""
    _startlist = await StartlistsAdapter.get_startlists_by_event_id(db, event_id)
    if _startlist:
        raise StartlistAllreadyExistException(
            f'Event "{event_id!r}" already has a startlist.'
        )


async def get_raceplan(db: Any, token: str, event_id: str) -> Raceplan:
    """Check if the event has a raceplan."""
    raceplans = await RaceplansAdapter.get_raceplans_by_event_id(db, event_id)
    if len(raceplans) == 0:
        raise NoRaceplanInEventException(
            f"No raceplan for event {event_id}. Cannot proceed."
        )
    if len(raceplans) > 1:
        raise DuplicateRaceplansInEventException(
            f"Multiple raceplans for event {event_id}. Cannot proceed."
        )
    return raceplans[0]


async def get_races(
    db: Any, token: str, raceplan_id: str
) -> List[Union[IndividualSprintRace, IntervalStartRace]]:
    """Check if the event has a races."""
    races = await RacesAdapter.get_races_by_raceplan_id(db, raceplan_id)
    if len(races) == 0:
        raise NoRacesInRaceplanException(
            f"No races in raceplan {raceplan_id}. Cannot proceed."
        )
    return races


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
    if competition_format["name"] == "Interval Start":
        if "intervals" not in competition_format:
            raise MissingPropertyException(
                f'Competition format "{competition_format_name!r}" '
                'is missing the "intervals" property.'
            ) from None
        # We do have intervals, check if valid format:
        await check_time(competition_format["intervals"])

    return competition_format


async def get_raceclasses(token: str, event_id: str) -> List[dict]:
    """Get the raceclasses in the event."""
    try:
        raceclasses = await EventsAdapter.get_raceclasses(token, event_id)
    except RaceclassesNotFoundException as e:
        raise e from e
    if not raceclasses or len(raceclasses) == 0:
        raise RaceclassesNotFoundException(
            f"No raceclasses found for event {event_id}."
        ) from None
    # Validate:
    pass

    return raceclasses


async def get_contestants(token: str, event_id: str) -> List[dict]:
    """Get the contestants in the event."""
    try:
        contestants = await EventsAdapter.get_contestants(token, event_id)
    except ContestantsNotFoundException as e:
        raise e from e
    if not contestants or len(contestants) == 0:
        raise ContestantsNotFoundException(
            f"No contestants found for event {event_id}."
        ) from None
    # Validate:
    # Check if contestants have only integers bib values:
    if not all(isinstance(o, (int)) for o in [c.get("bib", None) for c in contestants]):
        raise InconsistentValuesInContestantsException(
            f"Contestants bib values for event {event_id} contains non numeric values."
        )
    if len(contestants) != len(set([c["bib"] for c in contestants])):
        raise InconsistentValuesInContestantsException(
            f"Contestants bib values for event {event_id} are not unique."
        )

    return contestants
