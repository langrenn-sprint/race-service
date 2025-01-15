"""Raceplan data class module."""

from dataclasses import dataclass, field
from datetime import datetime

from dataclasses_json import DataClassJsonMixin, config
from marshmallow.fields import DateTime


@dataclass
class Changelog(DataClassJsonMixin):
    """Data class with representing a changelog."""

    timestamp: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=DateTime(format="iso"),
        )
    )
    user_id: str
    comment: str
