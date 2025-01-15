"""Raceplan data class module."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum

from dataclasses_json import DataClassJsonMixin, config
from marshmallow.fields import Constant, DateTime


class RaceResultStatus(IntEnum):
    """Valid values for a raceresult status."""

    NONE = 0
    UNOFFICIAL = 1
    OFFICIAL = 2


@dataclass
class RaceResult(DataClassJsonMixin):
    """Data class with details about a race-result."""

    id: str
    race_id: str
    timing_point: str
    no_of_contestants: int
    ranking_sequence: list[str]  # list of references to TimeEvent
    status: int  # int with reference to RaceResultStatus


@dataclass
class Race(DataClassJsonMixin):
    """Data class with details about a race."""

    id: str
    raceclass: str
    order: int
    start_time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=DateTime(format="iso"),
        )
    )
    max_no_of_contestants: int
    no_of_contestants: int
    event_id: str
    raceplan_id: str
    start_entries: list[str]  # list of references to StartEntry
    results: dict[str, str]  # dict with reference to RaceResult pr timing point


@dataclass
class IntervalStartRace(Race, DataClassJsonMixin):
    """Data class with details about a race."""

    datatype: str = field(
        metadata={"marshmallow_field": Constant("interval_start")},
        default="interval_start",
    )


@dataclass
class IndividualSprintRace(Race, DataClassJsonMixin):
    """Data class with details about a race."""

    round: str = ""
    index: str = ""
    heat: int = 0
    rule: dict[str, dict[str, int | str]] = field(default_factory=dict)
    datatype: str = field(
        metadata={"marshmallow_field": Constant("individual_sprint")},
        default="individual_sprint",
    )
