"""Module for raceplan commands."""
from datetime import date, time
from typing import Any, List

from race_service.adapters import (
    EventNotFoundException,
    EventsAdapter,
    FormatConfigurationNotFoundException,
    RaceplansAdapter,
)
from race_service.services import (
    RaceplanAllreadyExistException,
    RaceplansService,
)
from .exceptions import (
    CompetitionFormatNotSupportedException,
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
    async def generate_raceplan_for_event(
        cls: Any, db: Any, token: str, event_id: str
    ) -> str:
        """Generate raceplan for event function."""
        # First we check if event already has a plan:
        await get_raceplan(db, token, event_id)
        # First we get the event from the event-service:
        event = await get_event(token, event_id)
        # We fetch the configuration of the competition-format:
        format_configuration = await get_format_configuration(
            token, event["competition_format"]
        )
        # Then we fetch the raceclasses:
        raceclasses = await get_raceclasses(token, event_id)

        # Calculate the raceplan:
        if event["competition_format"] == "Individual Sprint":
            raceplan = await calculate_raceplan_individual_sprint(
                event, format_configuration, raceclasses
            )  # pragma: no cover
        elif event["competition_format"] == "Interval Start":
            raceplan = await calculate_raceplan_interval_start(
                event, format_configuration, raceclasses
            )
        # Finally we store the new raceplan and return the id:
        raceplan_id = await RaceplansService.create_raceplan(db, raceplan)
        assert raceplan_id
        return raceplan_id


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
    if competition_format.lower() == "Interval Start".lower():
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
