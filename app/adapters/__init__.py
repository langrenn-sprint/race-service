"""Package for all adapters."""

from .events_adapter import (
    CompetitionFormatNotFoundError,
    ContestantsNotFoundError,
    EventNotFoundError,
    EventsAdapter,
    EventsAdapterError,
    RaceclassesNotFoundError,
)
from .liveness_adapter import LivenessAdapter
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

__all__ = [
    "CompetitionFormatNotFoundError",
    "ContestantsNotFoundError",
    "EventNotFoundError",
    "EventsAdapter",
    "EventsAdapterError",
    "LivenessAdapter",
    "NotSupportedRaceDatatypeError",
    "RaceNotFoundError",
    "RaceResultNotFoundError",
    "RaceResultsAdapter",
    "RaceclassesNotFoundError",
    "RaceplanNotFoundError",
    "RaceplansAdapter",
    "RacesAdapter",
    "StartEntriesAdapter",
    "StartEntryNotFoundError",
    "StartlistNotFoundError",
    "StartlistsAdapter",
    "TimeEventNotFoundError",
    "TimeEventsAdapter",
]
