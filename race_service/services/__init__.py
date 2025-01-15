"""Package for all services."""

from .exceptions import IllegalValueError
from .race_results_service import (
    ContestantNotInStartEntriesError,
    RaceResultsService,
    TimeEventDoesNotReferenceRaceError,
    TimeEventIsNotIdentifiableError,
)
from .raceplans_service import (
    RaceplanAllreadyExistError,
    RaceplansService,
)
from .races_service import (
    RaceNotFoundError,
    RacesService,
)
from .start_entries_service import (
    CouldNotCreateStartEntryError,
    StartEntriesService,
)
from .startlists_service import (
    CouldNotCreateStartlistError,
    StartlistAllreadyExistError,
    StartlistsService,
)
from .time_events_service import (
    CouldNotCreateTimeEventError,
    TimeEventAllreadyExistError,
    TimeEventNotFoundError,
    TimeEventsService,
)

__all__ = [
    "ContestantNotInStartEntriesError",
    "CouldNotCreateStartEntryError",
    "CouldNotCreateStartlistError",
    "CouldNotCreateTimeEventError",
    "IllegalValueError",
    "RaceNotFoundError",
    "RaceResultsService",
    "RaceplanAllreadyExistError",
    "RaceplansService",
    "RacesService",
    "StartEntriesService",
    "StartlistAllreadyExistError",
    "StartlistsService",
    "TimeEventAllreadyExistError",
    "TimeEventDoesNotReferenceRaceError",
    "TimeEventIsNotIdentifiableError",
    "TimeEventNotFoundError",
    "TimeEventsService",
]
