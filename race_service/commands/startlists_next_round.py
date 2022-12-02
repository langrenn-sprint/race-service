"""Module for startlist commands."""
from datetime import date, time, timedelta
from typing import Any, Dict, List, Tuple, Union

from race_service.adapters import (
    CompetitionFormatNotFoundException,
    ContestantsNotFoundException,
    EventNotFoundException,
    EventsAdapter,
    RaceclassesNotFoundException,
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
    RaceplansService,
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
    StartlistNotFoundError,
)


async def generate_startlist_for_next_round_in_raceclass(  # noqa: C901
    db: Any, token: str, event_id: str, raceclass: Dict, this_round: str
) -> None:
    """Generate startlist for next round based on results in this round function."""
    # First we check if event has a startlist:
    try:
        startlist = await get_startlist(db, token, event_id)
    except StartlistNotFoundError as e:
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
    # Then we fetch the raceplan:
    raceplan = await get_raceplan(db, token, event_id)
    # and the races:
    if raceplan.id:
        races = await get_races(db, token, raceplan.id)

    # We are ready to generate the startlist:
    startlist, start_entries = await create_start_entries_for_individual_sprint(
        event,
        competition_format,
        raceclass,
        races,  # type: ignore
    )

    # We create each start_entry:
    assert startlist.id
    for start_entry in start_entries:
        start_entry.startlist_id = startlist.id
        start_entry_id = await StartEntriesService.create_start_entry(db, start_entry)
        startlist.start_entries.append(start_entry_id)

        # We add the start-entry to the respective race:
        race = await RacesService.get_race_by_id(db, start_entry.race_id)
        race.start_entries.append(start_entry_id)
        await RacesService.update_race(db, race.id, race)
    await StartlistsService.update_startlist(db, startlist.id, startlist)


async def create_start_entries_for_individual_sprint(  # noqa: C901
    event: Dict,
    competition_format: Dict,
    raceclass: Dict,
    races: List[IndividualSprintRace],
) -> List[StartEntry]:
    """Create a start-entries for an individual sprint event."""
    start_entries: List[StartEntry] = []

    #
    # For every race in first rounds (ranked classes) or all rounds (non ranked classes)
    # in raceplan grouped by raceclass,
    # get the corresponding ageclasses from raceclass,
    # pick all contestants in ageclasses,
    # and for every such contestant, generate a start_entry.
    # until race is full.

    # First we need to group the races by raceclass:
    d: Dict[str, list] = {}
    for _race in races:
        d.setdefault(_race.raceclass, []).append(_race)
    races_grouped_by_raceclass = list(d.values())

    for races_in_raceclass in races_grouped_by_raceclass:
        # We find the actual ageclasses in this raceclass:
        ageclasses: List[str] = []
        for raceclass in raceclasses:
            if raceclass["name"] == races_in_raceclass[0].raceclass:
                ranking = raceclass["ranking"]
                ageclasses += raceclass["ageclasses"]

        # For every contestant in corresponding ageclasses, create a start_entry in
        # a race until it is full, continue with next race:
        # Get the actual relevant races and set up control variables:
        if ranking:
            target_races = [
                race
                for race in races_in_raceclass
                if race.round == competition_format["rounds_ranked_classes"][0]
            ]
        else:
            target_races = [
                race
                for race in races_in_raceclass
                if race.round in [competition_format["rounds_non_ranked_classes"][0]]
            ]
        race_index = 0
        starting_position = 1
        no_of_contestants_in_race = 0

        for contestant in [
            contestant
            for contestant in contestants
            if contestant["ageclass"] in ageclasses
        ]:

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

        # For not ranked ageclasses we generate round 2 also:
        # TODO: This should be based on the races in first round, not contestants.
        # Consequently, we should move it out of this module into a separate one: generate_round_n_startlist
        target_races = [
            race
            for race in races_in_raceclass
            if race.round in [competition_format["rounds_non_ranked_classes"][1]]
        ]
        race_index = 0
        starting_position = 1
        no_of_contestants_in_race = 0
        if not ranking:
            for contestant in [
                contestant
                for contestant in contestants
                if contestant["ageclass"] in ageclasses
            ]:

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

    return start_entries


# helpers
async def get_startlist(db: Any, token: str, event_id: str) -> Startlist:
    """Check if the event already has a startlist."""
    _startlist = await StartlistsService.get_startlist_by_event_id(db, event_id)
    if len(_startlist) == 0:
        raise StartlistNotFoundError(f'Event "{event_id}" has no startlist.')
    if len(_startlist) > 1:
        raise StartlistAmbigiousError(
            f'Event "{event_id}" already has more than one startlist.'
        )
    return _startlist[0]


async def get_raceplan(db: Any, token: str, event_id: str) -> Raceplan:
    """Check if the event has a raceplan."""
    raceplans = await RaceplansService.get_raceplan_by_event_id(db, event_id)
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
    races = await RacesService.get_races_by_raceplan_id(db, raceplan_id)
    if len(races) == 0:
        raise NoRacesInRaceplanException(
            f"No races in raceplan {raceplan_id}. Cannot proceed."
        )
    return races


async def get_event(token: str, event_id: str) -> Dict:
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
            f'Date "{date_str}" has invalid format".'
        ) from e


async def check_time(time_str: str) -> None:
    """Validate time from string."""
    try:
        time.fromisoformat(time_str)
    except ValueError as e:
        raise InvalidDateFormatException('Time "{time_str}" has invalid format.') from e


async def get_competition_format(
    token: str, event_id: str, competition_format_name: str
) -> Dict:
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
                f'Competition format "{competition_format_name}" '
                'is missing the "intervals" property.'
            ) from None
        # We do have intervals, check if valid format:
        await check_time(competition_format["intervals"])

    return competition_format
