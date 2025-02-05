"""Raceplan data class module."""

from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin


@dataclass
class Raceplan(DataClassJsonMixin):
    """Data class with details about a raceplan."""

    event_id: str
    races: list[str]  # ids to every race in this plan
    no_of_contestants: int = 0
    id: str | None = field(default=None)
