"""Module for startlist commands."""

from datetime import date, time, timedelta
from typing import Any

from race_service.adapters import (
    CompetitionFormatNotFoundError,
    ContestantsNotFoundError,
    EventNotFoundError,
    EventsAdapter,
    RaceclassesNotFoundError,
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
    StartlistAllreadyExistError,
    StartlistsService,
)

from .exceptions import (
    CompetitionFormatNotSupportedError,
    DuplicateRaceplansInEventError,
    InconsistentInputDataError,
    InconsistentValuesInContestantsError,
    InvalidDateFormatError,
    MissingPropertyError,
    NoRaceplanInEventError,
    NoRacesInRaceplanError,
)


async def generate_startlist_for_event(  # noqa: C901
    db: Any, token: str, event_id: str
) -> str:
    """Generate startlist for event function."""
    # First we check if event already has a startlist:
    try:
        await get_startlist(db, token, event_id)
    except StartlistAllreadyExistError as e:
        raise e from e
    # Then we get the event from the event-service:
    try:
        event = await get_event(token, event_id)
    except EventNotFoundError as e:
        raise e from e
    # We fetch the competition-format:
    try:
        competition_format = await get_competition_format(
            token, event_id, event["competition_format"]
        )
    except CompetitionFormatNotFoundError as e:
        msg = f"Competition-format {event['competition_format']} is not supported."
        raise CompetitionFormatNotSupportedError(msg) from e
    # Then we fetch the raceclasses:
    raceclasses = await get_raceclasses(token, event_id)
    # Then we fetch the raceplan:
    try:
        raceplan = await get_raceplan(db, token, event_id)
    except NoRaceplanInEventError as e:
        raise e from e
    # and the races:
    try:
        races = await get_races(db, raceplan.id)  # type: ignore [reportArgumentType]
    except NoRacesInRaceplanError as e:
        raise e from e
    # And finally we get the list of contestants:
    contestants = await get_contestants(token, event_id)

    # Sanity check:
    no_of_contestants_in_raceclasses = sum(
        raceclass["no_of_contestants"] for raceclass in raceclasses
    )
    if len(contestants) != no_of_contestants_in_raceclasses:
        msg = (
            "Number of contestants in event does not match number of contestants in raceclasses:"
            f"{len(contestants)} != {no_of_contestants_in_raceclasses}."
        )
        raise InconsistentInputDataError(msg)
    if len(contestants) != raceplan.no_of_contestants:
        msg = (
            "Number of contestants in event does not match number of contestants in raceplan:"
            f"{len(contestants)} != {raceplan.no_of_contestants}."
        )
        raise InconsistentInputDataError(msg)

    # We are ready to generate the startlist:
    startlist = Startlist(
        event_id=event["id"],
        no_of_contestants=len(contestants),
        start_entries=[],
    )
    startlist_id = await StartlistsService.create_startlist(db, startlist)

    # And then generate the list of start-entries:
    if event["competition_format"] == "Individual Sprint":
        start_entries = await generate_start_entries_for_individual_sprint(
            competition_format,
            raceclasses,
            races,  # type: ignore [reportArgumentType]
            contestants,
        )

    elif event["competition_format"] == "Interval Start":
        start_entries = await generate_start_entries_for_interval_start(
            competition_format,
            raceclasses,
            races,  # type: ignore [reportArgumentType]
            contestants,
        )
    else:
        msg = f'Competition-format "{event["competition_format"]!r}" not supported.'
        raise CompetitionFormatNotSupportedError(msg)

    # We create each start_entry and add it to the startlist:
    for start_entry in start_entries:
        start_entry.startlist_id = startlist_id
        start_entry_id = await StartEntriesService.create_start_entry(db, start_entry)
        startlist.start_entries.append(start_entry_id)

        # We add the start-entry to the respective race:
        race = await RacesAdapter.get_race_by_id(db, start_entry.race_id)
        race.start_entries.append(start_entry_id)
        await RacesService.update_race(db, race.id, race)
    await StartlistsService.update_startlist(db, startlist_id, startlist)

    return startlist_id


async def generate_start_entries_for_individual_sprint(  # noqa: PLR0912, C901
    competition_format: dict,
    raceclasses: list[dict],
    races: list[IndividualSprintRace],
    contestants: list[dict],
) -> list[StartEntry]:
    """Generate a startlist for an individual sprint event."""
    start_entries: list[StartEntry] = []
    # Check that the number of contestants in the races matches the number of contestants
    no_of_contestants_in_races = sum(
        race.no_of_contestants
        for race in races
        if race.round
        in [
            competition_format["rounds_ranked_classes"][0],
            competition_format["rounds_non_ranked_classes"][0],
        ]
    )
    if len(contestants) != no_of_contestants_in_races:
        msg = (
            "Number of contestants in event does not match sum of contestants in races:"
            f"{len(contestants)} != {no_of_contestants_in_races}."
        )
        raise InconsistentInputDataError(msg)
    #
    # For every race in first rounds (ranked classes) or all rounds (non ranked classes)
    # in raceplan grouped by raceclass,
    # get the corresponding ageclasses from raceclass,
    # pick all contestants in ageclasses,
    # and for every such contestant, generate a start_entry.
    # until race is full.

    # First we need to group the races by raceclass:
    d: dict[str, list] = {}
    for _race in races:
        d.setdefault(_race.raceclass, []).append(_race)
    races_grouped_by_raceclass = list(d.values())

    for races_in_raceclass in races_grouped_by_raceclass:
        # We find the actual ageclasses in this raceclass:
        ageclasses: list[str] = []
        ranking: bool = True
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
                if race.round == competition_format["rounds_non_ranked_classes"][0]
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
                name=f"{contestant['first_name']} {contestant['last_name']}",
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
        # TODO: Base this on the races in first round, not contestants: # noqa: TD002, TD003, FIX002
        target_races = [
            race
            for race in races_in_raceclass
            if race.round == competition_format["rounds_non_ranked_classes"][1]
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
                    name=f"{contestant['first_name']} {contestant['last_name']}",
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


async def generate_start_entries_for_interval_start(
    competition_format: dict,
    raceclasses: list[dict],
    races: list[IntervalStartRace],
    contestants: list[dict],
) -> list[StartEntry]:
    """Generate a startlist for an interval start event."""
    start_entries: list[StartEntry] = []
    # Check that the number of contestants in the races matches the number of contestants
    no_of_contestants_in_races = sum(race.no_of_contestants for race in races)
    if len(contestants) != no_of_contestants_in_races:
        msg = (
            "Number of contestants in event does not match sum of contestants in races:"
            f"{len(contestants)} != {no_of_contestants_in_races}."
        )
        raise InconsistentInputDataError(msg)
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
    d: dict[str, list] = {}
    for _race in races:
        d.setdefault(_race.raceclass, []).append(_race)
    races_grouped_by_raceclass = list(d.values())

    for races_in_raceclass in races_grouped_by_raceclass:
        for race in races_in_raceclass:
            starting_position = 1
            # Get the correponding ageclasses:
            ageclasses: list[str] = []
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
                start_entry = StartEntry(
                    id="",
                    startlist_id="",
                    race_id=race.id,
                    bib=contestant["bib"],
                    name=f"{contestant['first_name']} {contestant['last_name']}",
                    club=contestant["club"],
                    starting_position=starting_position,
                    scheduled_start_time=scheduled_start_time,
                )
                scheduled_start_time = scheduled_start_time + interval
                start_entries.append(start_entry)

                starting_position += 1

    return start_entries


# helpers
async def get_startlist(db: Any, token: str, event_id: str) -> None:
    """Check if the event already has a startlist."""
    del token  # for now we do not use token
    _startlist = await StartlistsAdapter.get_startlists_by_event_id(db, event_id)
    if _startlist:
        msg = f'Event "{event_id!r}" already has a startlist.'
        raise StartlistAllreadyExistError(msg)


async def get_raceplan(db: Any, token: str, event_id: str) -> Raceplan:
    """Check if the event has a raceplan."""
    del token  # for now we do not use token
    raceplans = await RaceplansAdapter.get_raceplans_by_event_id(db, event_id)
    if len(raceplans) == 0:
        msg = f"No raceplan for event {event_id}. Cannot proceed."
        raise NoRaceplanInEventError(msg)
    if len(raceplans) > 1:
        msg = f"Multiple raceplans for event {event_id}. Cannot proceed."
        raise DuplicateRaceplansInEventError(msg)
    return raceplans[0]


async def get_races(
    db: Any, raceplan_id: str
) -> list[IndividualSprintRace | IntervalStartRace]:
    """Check if the event has a races."""
    races = await RacesAdapter.get_races_by_raceplan_id(db, raceplan_id)
    if len(races) == 0:
        msg = f"No races in raceplan {raceplan_id}. Cannot proceed."
        raise NoRacesInRaceplanError(msg)
    return races


async def get_event(token: str, event_id: str) -> dict:
    """Get the event and validate."""
    try:
        event = await EventsAdapter.get_event_by_id(token, event_id)
    except EventNotFoundError as e:
        raise e from e
    # Check if the event has a competition-format:
    if "competition_format" not in event:
        msg = f"Event {event_id} has no value for competition_format."
        raise CompetitionFormatNotSupportedError(msg) from None

    # We check if event has valid date:
    if "date_of_event" in event:
        await check_date(event["date_of_event"])
    else:
        msg = 'Event does not have a value for "date_of_event".'
        raise MissingPropertyError(msg) from None

    if "time_of_event" in event:
        await check_time(event["time_of_event"])
    else:
        msg = 'Event does not have a value for "time_of_event".'
        raise MissingPropertyError(msg) from None

    return event


async def check_date(date_str: str) -> None:
    """Validate date from string."""
    try:
        date.fromisoformat(date_str)
    except ValueError as e:
        msg = f'Date "{date_str!r}" has invalid format".'
        raise InvalidDateFormatError(msg) from e


async def check_time(time_str: str) -> None:
    """Validate time from string."""
    try:
        time.fromisoformat(time_str)
    except ValueError as e:
        msg = 'Time "{time_str}" has invalid format.'
        raise InvalidDateFormatError(msg) from e


async def get_competition_format(
    token: str, event_id: str, competition_format_name: str
) -> dict:
    """Get the competition-format."""
    try:
        competition_format = await EventsAdapter.get_competition_format(
            token, event_id, competition_format_name
        )
    except CompetitionFormatNotFoundError as e:
        raise e from e
    # Validate:
    if competition_format["name"] == "Interval Start":
        if "intervals" not in competition_format:
            msg = (
                f'Competition format "{competition_format_name!r}" '
                'is missing the "intervals" property.'
            )
            raise MissingPropertyError(msg) from None
        # We do have intervals, check if valid format:
        await check_time(competition_format["intervals"])

    return competition_format


async def get_raceclasses(token: str, event_id: str) -> list[dict]:
    """Get the raceclasses in the event."""
    try:
        raceclasses = await EventsAdapter.get_raceclasses(token, event_id)
    except RaceclassesNotFoundError as e:
        raise e from e
    if not raceclasses or len(raceclasses) == 0:
        msg = f"No raceclasses found for event {event_id}."
        raise RaceclassesNotFoundError(msg) from None
    # Validate:

    return raceclasses


async def get_contestants(token: str, event_id: str) -> list[dict]:
    """Get the contestants in the event."""
    try:
        contestants = await EventsAdapter.get_contestants(token, event_id)
    except ContestantsNotFoundError as e:
        raise e from e
    if not contestants or len(contestants) == 0:
        msg = f"No contestants found for event {event_id}."
        raise ContestantsNotFoundError(msg) from None
    # Validate:
    # Check if contestants have only integers bib values:
    if not all(isinstance(o, (int)) for o in [c.get("bib", None) for c in contestants]):
        msg = (
            f"Contestants bib values for event {event_id} contains non numeric values."
        )
        raise InconsistentValuesInContestantsError(msg)
    if len(contestants) != len({c["bib"] for c in contestants}):
        msg = f"Contestants bib values for event {event_id} are not unique."
        raise InconsistentValuesInContestantsError(msg)

    return contestants
