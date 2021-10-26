"""Module for startlist commands."""
from datetime import date, time, timedelta
from typing import Any, List

from race_service.adapters import (
    ContestantsNotFoundException,
    EventNotFoundException,
    EventsAdapter,
    FormatConfigurationNotFoundException,
    RaceclassesNotFoundException,
    StartlistsAdapter,
)
from race_service.models import Raceplan, StartEntry, Startlist
from race_service.services import (
    RaceplansService,
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
)


class StartlistsCommands:
    """Class representing a commands on events."""

    @classmethod
    async def generate_startlist_for_event(
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
        # We fetch the configuration of the competition-format:
        try:
            format_configuration = await get_format_configuration(
                token, event_id, event["competition_format"]
            )
        except FormatConfigurationNotFoundException as e:
            raise CompetitionFormatNotSupportedException(
                f'Competition-format {event["competition_format"]} is not supported.'
            ) from e
        # Then we fetch the raceclasses:
        raceclasses = await get_raceclasses(token, event_id)
        # Then we fetch the raceplan:
        raceplan = await get_raceplan(db, token, event_id)
        # And finally we get the list of contestants:
        contestants = await get_contestants(token, event_id)

        # We are ready to generate the raceplan:
        startlist = None
        if event["competition_format"] == "Individual Sprint":
            startlist = await generate_startlist_for_individual_sprint(
                event,
                format_configuration,
                raceclasses,
                raceplan,
                contestants,
            )
        elif event["competition_format"] == "Interval Start":
            startlist = await generate_startlist_for_interval_start(
                event,
                format_configuration,
                raceclasses,
                raceplan,
                contestants,
            )
        # Finally we store the new raceplan and return the id:
        assert startlist
        startlist_id = await StartlistsService.create_startlist(db, startlist)
        assert startlist_id
        return startlist_id


async def generate_startlist_for_individual_sprint(
    event: dict,
    format_configuration: dict,
    raceclasses: List[dict],
    raceplan: Raceplan,
    contestants: List[dict],
) -> Startlist:  # pragma: no cover
    """Generate a startlist for an individual sprint event."""
    no_of_contestants = len(contestants)
    start_entries: List[StartEntry] = []
    startlist = Startlist(
        event_id=event["id"],
        no_of_contestants=no_of_contestants,
        start_entries=start_entries,
    )

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
            f"{len(contestants)} != {no_of_contestants_in_raceclasses}."
        )
    #
    no_of_contestants_in_races = sum(
        race.no_of_contestants for race in raceplan.races if race.round == "Q"
    )
    if len(contestants) != no_of_contestants_in_races:
        raise InconsistentInputDataException(
            "len(contestants) does not match sum of contestants in raceplan.races quarterfinals:"
            f"{len(contestants)} != {no_of_contestants_in_races}."
        )
    #
    # For every race in round=Q in raceplan grouped by raceclass,
    # get the corresponding ageclasses from raceclass,
    # pick all contestants in ageclasses,
    # and for every such contestant, generate a start_entry.
    # until race is full.

    # First we need to group the races by raceclass:
    d: dict[str, list] = {}
    for race in raceplan.races:
        d.setdefault(race.raceclass, []).append(race)
    races_grouped_by_raceclass = list(d.values())

    for races in races_grouped_by_raceclass:
        # We find the actual ageclasses in this raceclass:
        ageclasses = [
            raceclass["ageclass_name"]
            for raceclass in raceclasses
            if raceclass["name"] == races[0].raceclass
        ]
        # For every contestant in ageclass, create a start_entry in
        # a quarter-final until it is full, continue with next quarter-final:

        # Get the actual quarter-finals and set up control variables:
        quarter_finals = [race for race in races if race.round == "Q"]
        qf_index = 0
        starting_position = 1
        no_of_contestants_in_qf = 0

        for contestant in [
            contestant
            for contestant in contestants
            if contestant["ageclass"] in ageclasses
        ]:

            # Create the start-entry:
            start_entry = StartEntry(
                id="",
                race_id=quarter_finals[qf_index].id,
                bib=contestant["bib"],
                starting_position=starting_position,
                scheduled_start_time=quarter_finals[qf_index].start_time,
            )
            startlist.start_entries.append(start_entry)

            no_of_contestants_in_qf += 1
            # Check if qf is full:
            if no_of_contestants_in_qf < quarter_finals[qf_index].no_of_contestants:
                starting_position += 1
            else:
                qf_index += 1
                starting_position = 1
                no_of_contestants_in_qf = 0

    return startlist


async def generate_startlist_for_interval_start(
    event: dict,
    format_configuration: dict,
    raceclasses: List[dict],
    raceplan: Raceplan,
    contestants: List[dict],
) -> Startlist:
    """Generate a startlist for an interval start event."""
    no_of_contestants = len(contestants)
    start_entries: List[StartEntry] = []
    startlist = Startlist(
        event_id=event["id"],
        no_of_contestants=no_of_contestants,
        start_entries=start_entries,
    )
    interval = timedelta(
        hours=time.fromisoformat(format_configuration["intervals"]).hour,
        minutes=time.fromisoformat(format_configuration["intervals"]).minute,
        seconds=time.fromisoformat(format_configuration["intervals"]).second,
    )
    # For every race in raceplan grouped by raceclass,
    # get the corresponding ageclasses from raceclass,
    # pick all contestants in ageclasses,
    # and for every such contestant, generate a start_entry:

    # First we need to group the races by raceclass:
    d: dict[str, list] = {}
    for race in raceplan.races:
        d.setdefault(race.raceclass, []).append(race)
    races_grouped = list(d.values())

    for races in races_grouped:
        for race in races:
            starting_position = 0
            # Get the correponding ageclasses:
            ageclasses = [
                raceclass["ageclass_name"]
                for raceclass in raceclasses
                if raceclass["name"] == race.raceclass
            ]
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
                    race_id=race.id,
                    bib=bib,
                    starting_position=starting_position,
                    scheduled_start_time=scheduled_start_time,
                )
                scheduled_start_time = scheduled_start_time + interval
                startlist.start_entries.append(start_entry)

    return startlist


# helpers
async def get_startlist(db: Any, token: str, event_id: str) -> None:
    """Check if the event already has a startlist."""
    _startlist = await StartlistsAdapter.get_startlist_by_event_id(db, event_id)
    if _startlist:
        raise StartlistAllreadyExistException(
            f'Event "{event_id}" already has a raceplan.'
        )


async def get_raceplan(db: Any, token: str, event_id: str) -> Raceplan:
    """Check if the event already has a raceplan."""
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


async def get_event(token: str, event_id: str) -> dict:
    """Get the event and validate."""
    try:
        event = await EventsAdapter.get_event_by_id(token, event_id)
    except EventNotFoundException as e:
        raise e from e
    # Check if the event has a competition format:
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


async def get_format_configuration(
    token: str, event_id: str, competition_format_name: str
) -> dict:
    """Get the format configuration."""
    try:
        format_configuration = await EventsAdapter.get_format_configuration(
            token, event_id, competition_format_name
        )
    except FormatConfigurationNotFoundException as e:
        raise e from e
    # Validate:
    if format_configuration["name"] == "Interval Start":
        if "intervals" not in format_configuration:
            raise MissingPropertyException(
                f'Format configuration "{competition_format_name}" '
                'is missing the "intervals" property.'
            ) from None
        # We do have intervals, check if valid format:
        await check_time(format_configuration["intervals"])

    return format_configuration


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
