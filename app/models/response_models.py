"""Response models where references to other objects are expanded.

Each model overrides the reference fields of its base model (list of ids)
with the expanded objects. Pydantic supports this, but type checkers
flag it as an invalid override, hence the ignore comments.
"""

from typing import Annotated

from pydantic import Field

from .race_model import IndividualSprintRace, IntervalStartRace, RaceResult
from .raceplan_model import Raceplan
from .startlist_model import StartEntry, Startlist
from .time_event_model import TimeEvent


class RaceResultWithTimeEvents(RaceResult):
    """Race-result where the ranking-sequence is expanded to time-events."""

    ranking_sequence: list[TimeEvent]  # ty: ignore[invalid-attribute-override]


class IntervalStartRaceWithDetails(IntervalStartRace):
    """Interval start race with expanded start-entries and results."""

    start_entries: list[StartEntry]  # ty: ignore[invalid-attribute-override]
    results: dict[str, RaceResultWithTimeEvents]  # ty: ignore[invalid-attribute-override]


class IndividualSprintRaceWithDetails(IndividualSprintRace):
    """Individual sprint race with expanded start-entries and results."""

    start_entries: list[StartEntry]  # ty: ignore[invalid-attribute-override]
    results: dict[str, RaceResultWithTimeEvents]  # ty: ignore[invalid-attribute-override]


RaceWithDetailsUnion = Annotated[
    IndividualSprintRaceWithDetails | IntervalStartRaceWithDetails,
    Field(discriminator="datatype"),
]


class RaceplanWithRaces(Raceplan):
    """Raceplan where the races are expanded."""

    races: list[IndividualSprintRace | IntervalStartRace]  # ty: ignore[invalid-attribute-override]


class StartlistWithStartEntries(Startlist):
    """Startlist where the start-entries are expanded."""

    start_entries: list[StartEntry]  # ty: ignore[invalid-attribute-override]
