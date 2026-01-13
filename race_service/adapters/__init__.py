"""Package for all adapters."""

from .events_adapter import (
    CompetitionFormatNotFoundError,
    ContestantsNotFoundError,
    EventNotFoundError,
    EventsAdapter,
    RaceclassesNotFoundError,
    RaceclassNotFoundError,
)
from .race_results_adapter import RaceResultNotFoundError, RaceResultsAdapter
from .raceplans_adapter import RaceplanNotFoundError, RaceplansAdapter
from .races_adapter import (
    NotSupportedRaceDatatypeError,
    RaceNotFoundError,
    RacesAdapter,
)
from .start_entries_adapter import StartEntriesAdapter, StartEntryNotFoundError
from .startlists_adapter import StartlistNotFoundError, StartlistsAdapter
from .time_events_adapter import TimeEventNotFoundError, TimeEventsAdapter
from .users_adapter import UsersAdapter

__all__ = [
    "CompetitionFormatNotFoundError",
    "ContestantsNotFoundError",
    "EventNotFoundError",
    "EventsAdapter",
    "NotSupportedRaceDatatypeError",
    "RaceNotFoundError",
    "RaceResultNotFoundError",
    "RaceResultsAdapter",
    "RaceclassesNotFoundError",
    "RaceclassNotFoundError",
    "RaceplanNotFoundError",
    "RaceplansAdapter",
    "RacesAdapter",
    "StartEntriesAdapter",
    "StartEntryNotFoundError",
    "StartlistNotFoundError",
    "StartlistsAdapter",
    "TimeEventNotFoundError",
    "TimeEventsAdapter",
    "UsersAdapter",
]
