"""TimeEvent data class module."""
from dataclasses import dataclass, field
from datetime import time
from typing import List, Optional

from dataclasses_json import config, DataClassJsonMixin
from marshmallow.fields import Time

from .changelog import Changelog


@dataclass
class TimeEvent(DataClassJsonMixin):
    """Data class with details about a time_event."""

    bib: int
    event_id: str
    timing_point: str
    registration_time: time = field(
        metadata=config(
            encoder=time.isoformat,
            decoder=time.fromisoformat,
            mm_field=Time(format="iso"),
        )
    )
    name: Optional[str] = field(default=None)
    club: Optional[str] = field(default=None)
    race: Optional[str] = field(default=None)
    race_id: Optional[str] = field(default=None)
    rank: Optional[int] = field(default=None)
    next_race: Optional[str] = field(default=None)
    next_race_id: Optional[str] = field(default=None)
    next_race_position: Optional[int] = field(default=None)
    status: Optional[str] = field(default=None)
    changelog: Optional[List[Changelog]] = field(default=None)
    id: Optional[str] = field(default=None)
