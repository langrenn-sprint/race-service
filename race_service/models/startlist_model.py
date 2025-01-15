"""Raceplan data class module."""

from dataclasses import dataclass, field
from datetime import datetime

from dataclasses_json import DataClassJsonMixin, config
from marshmallow.fields import DateTime

from .changelog import Changelog


@dataclass
class StartEntry(DataClassJsonMixin):
    """Data class with details about a starlist."""

    startlist_id: str
    race_id: str
    bib: int
    starting_position: int
    scheduled_start_time: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=DateTime(format="iso"),
        )
    )
    name: str
    club: str
    status: str | None = field(default=None)
    changelog: list[Changelog] | None = field(default=None)
    id: str | None = field(default=None)


@dataclass
class Startlist(DataClassJsonMixin):
    """Data class with details about a starlist."""

    event_id: str
    no_of_contestants: int
    start_entries: list[str]
    id: str | None = field(default=None)
