"""Module for raceplan commands."""
from datetime import date, datetime, time, timedelta
import logging
from typing import Any, List

from race_service.adapters import (
    EventNotFoundException,
    EventsAdapter,
    FormatConfigurationNotFoundException,
)
from race_service.models import Race, Raceplan
from race_service.services import (
    RaceplansService,
)


class CompetitionFormatNotSupportedException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class NoRaceclassesInEventException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InconsistentValuesInRaceclassesException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class MissingPropertyException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InvalidDateFormatException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class RaceplansCommands:
    """Class representing a commands on events."""

    @classmethod
    async def generate_raceplan_for_event(
        cls: Any, db: Any, token: str, event_id: str
    ) -> str:
        """Generate raceplan for event function."""
        # First we get the event from the event-service:
        event = await get_event(token, event_id)
        # We fetch the configuration of the competition-format:
        format_configuration = await get_format_configuration(
            token, event["competition_format"]
        )
        # Then we fetch the raceclasses:
        raceclasses = await get_raceclasses(token, event_id)

        # Calculate the raceplan:
        raceplan = await calculate_raceplan(event, format_configuration, raceclasses)

        # Finally we store the new raceplan and return the id:
        raceplan_id = await RaceplansService.create_raceplan(db, raceplan)
        assert raceplan_id
        return raceplan_id


# calculations
async def calculate_raceplan(
    event: dict,
    format_configuration: dict,
    raceclasses: List[dict],
) -> Raceplan:
    """Calculate raceplan based on input."""
    logging.debug(f"Calculate raceplan for event: {event}")
    logging.debug(f"Calculate raceplan for competition_format: {format_configuration}")
    logging.debug(f"Calculate raceplan for raceclasses: {raceclasses}")
    raceplan = Raceplan(event_id=event["id"], races=list())
    # sort the raceclasses on order:
    raceclasses_sorted = sorted(raceclasses, key=lambda k: k["order"])
    # get the interval as timedelta:
    logging.debug(
        f'Format_configuration.intervals: {format_configuration["intervals"]}'
    )
    intervals = timedelta(
        hours=time.fromisoformat(format_configuration["intervals"]).hour,
        minutes=time.fromisoformat(format_configuration["intervals"]).minute,
        seconds=time.fromisoformat(format_configuration["intervals"]).second,
    )
    # get the first start_time from the event:
    logging.debug(
        f'Event.date/Event.time: {event["date_of_event"]}/{event["time_of_event"]}.'
    )
    start_time = datetime.combine(
        date.fromisoformat(event["date_of_event"]),
        time.fromisoformat(event["time_of_event"]),
    )

    for raceclass in raceclasses_sorted:
        race = Race(
            raceclass=raceclass["name"],
            order=raceclass["order"],
            start_time=start_time,
            no_of_contestants=raceclass["no_of_contestants"],
        )
        # Calculate start_time for next raceclass:
        start_time = start_time + intervals * raceclass["no_of_contestants"]
        # Add the race to the raceplan:
        raceplan.races.append(race)
        raceplan.no_of_contestants += race.no_of_contestants
    return raceplan


# helpers
async def get_event(token: str, event_id: str) -> dict:
    """Get the event and validate."""
    try:
        event = await EventsAdapter.get_event_by_id(token, event_id)
    except EventNotFoundException as e:
        raise e from e
    # Check if we support the competition format:
    try:
        competition_format = event["competition_format"]
    except KeyError as e:
        raise CompetitionFormatNotSupportedException(
            f"Event {event_id} has no value for competition_format."
        ) from e

    # We check if we support the competition-format:
    if competition_format.lower() == "Interval start".lower():
        pass
    else:
        raise CompetitionFormatNotSupportedException(
            f'Competition-format "{competition_format}" not supported.'
        )

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


async def get_format_configuration(token: str, competition_format_name: str) -> dict:
    """Get the format configuration."""
    try:
        format_configuration = await EventsAdapter.get_format_configuration(
            token, competition_format_name
        )
    except FormatConfigurationNotFoundException as e:
        raise e from e
    # Validate:
    if "intervals" not in format_configuration:
        raise MissingPropertyException(
            f'Format configuration "{competition_format_name}" '
            'is missing the "intervals" property.'
        )
    # We do have intervals, check if valid format:
    await check_time(format_configuration["intervals"])

    return format_configuration


async def get_raceclasses(token: str, event_id: str) -> List[dict]:
    """Get the raceclasses."""
    raceclasses = await EventsAdapter.get_raceclasses(token, event_id)
    # Validate:
    # Check if there in fact _are_ raceclasses in the list:
    if len(raceclasses) == 0:
        raise NoRaceclassesInEventException(
            f"No raceclass for event {event_id}. Cannot proceed."
        )

    # Check if raceclasses have only integers order values:
    if not all(
        isinstance(o, (int)) for o in [r.get("order", None) for r in raceclasses]
    ):
        raise InconsistentValuesInRaceclassesException(
            f"Raceclasses order values for event {event_id} contains non numeric values."
        )

    # Check if raceclasses have complete and unique values for `order`:
    if len(raceclasses) != len(set([r["order"] for r in raceclasses])):
        raise InconsistentValuesInRaceclassesException(
            f"Raceclasses order values for event {event_id} are not unique."
        )

    # Check if the order values are consecutive:
    if not sorted([r["order"] for r in raceclasses]) == list(
        range(
            min([r["order"] for r in raceclasses]),
            max([r["order"] for r in raceclasses]) + 1,
        )
    ):
        raise InconsistentValuesInRaceclassesException(
            f"Raceclasses order values for event {event_id} are not consecutive."
        )

    return raceclasses
