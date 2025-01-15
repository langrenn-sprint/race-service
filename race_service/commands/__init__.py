"""Package for all commands."""

from .exceptions import (
    CompetitionFormatNotSupportedError,
    CouldNotCreateRaceError,
    CouldNotCreateRaceplanError,
    DuplicateRaceplansInEventError,
    IllegalValueInRaceError,
    InconsistentInputDataError,
    InconsistentValuesInContestantsError,
    InconsistentValuesInRaceclassesError,
    InvalidDateFormatError,
    MissingPropertyError,
    NoRaceclassesInEventError,
    NoRaceplanInEventError,
    NoRacesInRaceplanError,
)
from .raceplans_commands import RaceplansCommands
from .startlists_commands import (
    generate_start_entries_for_individual_sprint,
    generate_start_entries_for_interval_start,
    generate_startlist_for_event,
)

__all__ = [
    "CompetitionFormatNotSupportedError",
    "CouldNotCreateRaceError",
    "CouldNotCreateRaceplanError",
    "DuplicateRaceplansInEventError",
    "IllegalValueInRaceError",
    "InconsistentInputDataError",
    "InconsistentValuesInContestantsError",
    "InconsistentValuesInRaceclassesError",
    "InvalidDateFormatError",
    "MissingPropertyError",
    "NoRaceclassesInEventError",
    "NoRaceplanInEventError",
    "NoRacesInRaceplanError",
    "RaceplansCommands",
    "generate_start_entries_for_individual_sprint",
    "generate_start_entries_for_interval_start",
    "generate_startlist_for_event",
]
