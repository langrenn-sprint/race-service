"""TimeEvent data class module."""

from dataclasses import dataclass, field
from datetime import datetime

from dataclasses_json import DataClassJsonMixin, config
from marshmallow.fields import DateTime

from .changelog import Changelog


@dataclass
class TimeEvent(DataClassJsonMixin):
    """Data class with details about a time_event."""

    bib: int
    event_id: str
    timing_point: str
    registration_time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=DateTime(format="iso"),
        )
    )
    name: str | None = field(default=None)
    club: str | None = field(default=None)
    race: str | None = field(default=None)
    race_id: str | None = field(default=None)
    rank: int | None = field(default=None)
    next_race: str | None = field(default=None)
    next_race_id: str | None = field(default=None)
    next_race_position: int | None = field(default=None)
    status: str | None = field(default=None)
    changelog: list[Changelog] | None = field(default=None)
    id: str | None = field(default=None)
