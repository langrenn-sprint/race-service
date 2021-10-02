"""Raceplan data class module."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from dataclasses_json import config, DataClassJsonMixin
from marshmallow import fields


@dataclass
class Race(DataClassJsonMixin):
    """Data class with details about a race."""

    raceclass: str
    order: int
    start_time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    no_of_contestants: int
    id: Optional[str] = field(default=None)


@dataclass
class IndividualSprintRace(Race, DataClassJsonMixin):
    """Data class with details about a race."""

    round: str = ""
    heat: int = 0


@dataclass
class Raceplan(DataClassJsonMixin):
    """Data class with details about a raceplan."""

    event_id: str
    races: List[Race]
    no_of_contestants: int = 0
    id: Optional[str] = field(default=None)
