"""Raceplan data class module."""
from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Race(DataClassJsonMixin):
    """Data class with details about a race."""

    raceclass: str
    order: int
    start_time: str
    no_of_contestants: int = 0
    heat: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)


@dataclass
class Raceplan(DataClassJsonMixin):
    """Data class with details about a raceplan."""

    event_id: str
    races: List[Race]
    no_of_contestants: int = 0
    id: Optional[str] = field(default=None)
