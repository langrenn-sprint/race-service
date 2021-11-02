"""Raceplan data class module."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Union

from dataclasses_json import config, DataClassJsonMixin
from marshmallow.fields import Constant, DateTime


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
    no_of_contestants: int
    event_id: str
    raceplan_id: str
    start_entries: List[str]


@dataclass
class IntervalStartRace(Race, DataClassJsonMixin):
    """Data class with details about a race."""

    datatype: str = field(
        metadata=dict(marshmallow_field=Constant("interval_start")),
        default="interval_start",
    )


@dataclass
class IndividualSprintRace(Race, DataClassJsonMixin):
    """Data class with details about a race."""

    round: str = ""
    index: str = ""
    heat: int = 0
    rule: Dict[str, Dict[str, Union[int, float]]] = field(default_factory=dict)
    datatype: str = field(
        metadata=dict(marshmallow_field=Constant("individual_sprint")),
        default="individual_sprint",
    )
