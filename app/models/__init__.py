"""Package for all models."""

from .changelog import Changelog
from .race_model import (
    IndividualSprintRace,
    IntervalStartRace,
    Race,
    RaceResult,
    RaceResultStatus,
    RaceUnion,
)
from .raceplan_model import Raceplan
from .response_models import (
    IndividualSprintRaceWithDetails,
    IntervalStartRaceWithDetails,
    RaceplanWithRaces,
    RaceResultWithTimeEvents,
    RaceWithDetailsUnion,
    StartlistWithStartEntries,
)
from .startlist_model import StartEntry, Startlist
from .time_event_model import TimeEvent

__all__ = [
    "Changelog",
    "IndividualSprintRace",
    "IndividualSprintRaceWithDetails",
    "IntervalStartRace",
    "IntervalStartRaceWithDetails",
    "Race",
    "RaceResult",
    "RaceResultStatus",
    "RaceResultWithTimeEvents",
    "RaceUnion",
    "RaceWithDetailsUnion",
    "Raceplan",
    "RaceplanWithRaces",
    "StartEntry",
    "Startlist",
    "StartlistWithStartEntries",
    "TimeEvent",
]
