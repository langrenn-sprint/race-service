"""TimeEvent data class module."""
from dataclasses import dataclass, field
from datetime import time
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class TimeEvent(DataClassJsonMixin):
    """Data class with details about a time_event."""

    bib: int
    event_id: Optional[str] = field(default=None)
    race_id: Optional[str] = field(default=None)
    point: Optional[str] = field(default=None)
    rank: Optional[str] = field(default=None)
    registration_time: Optional[time] = field(default=None)
    next_race_id: Optional[str] = field(default=None)
    next_race_position: Optional[int] = field(default=None)
    status: Optional[str] = field(default=None)
    changelog: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)
