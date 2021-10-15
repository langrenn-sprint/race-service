"""Raceplan data class module."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Union

from dataclasses_json import config, DataClassJsonMixin
from marshmallow.fields import Constant, DateTime


@dataclass
class Race(DataClassJsonMixin):
    """Data class with details about a race."""

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
    id: str


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


@dataclass
class Raceplan(DataClassJsonMixin):
    """Data class with details about a raceplan."""

    event_id: str
    races: List[Union[IntervalStartRace, IndividualSprintRace, Race]]
    no_of_contestants: int = 0
    id: Optional[str] = field(default=None)
