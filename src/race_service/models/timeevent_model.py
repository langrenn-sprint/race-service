"""Timeevent data class module."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from dataclasses_json import config, DataClassJsonMixin
from marshmallow.fields import DateTime


@dataclass
class Timeevent(DataClassJsonMixin):
    """Data class with details about a raceplan."""

    bib: int
    event_id: str
    race_id: str
    point: str
    rank: int
    registration_time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=DateTime(format="iso"),
        )
    )
    next_race_id: str
    status: str
    changelog: List[Dict]
    id: Optional[str] = field(default=None)
