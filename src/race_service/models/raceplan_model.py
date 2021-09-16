"""Raceplan data class module."""
from dataclasses import dataclass, field
from datetime import time
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Contestant(DataClassJsonMixin):
    """Data class with details about contestant."""

    bib: str
    startingposition: int


@dataclass
class Race(DataClassJsonMixin):
    """Data class with details about a race."""

    name: str
    raceclass: str
    order: int
    start_time: time
    id: Optional[str] = field(default=None)
    # contestants: Optional[List[Contestant]] = field(default=None)


@dataclass
class Raceplan(DataClassJsonMixin):
    """Data class with details about a raceplan."""

    event_id: str
    races: List[Race]
    id: Optional[str] = field(default=None)
