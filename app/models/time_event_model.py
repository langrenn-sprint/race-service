"""TimeEvent model module."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_serializer

from .changelog import Changelog


class TimeEvent(BaseModel):
    """Model with details about a time_event."""

    id: UUID = Field(default_factory=uuid4)
    bib: int
    event_id: UUID
    timing_point: str
    registration_time: datetime

    @field_serializer("registration_time")
    def serialize_registration_time(self, dt: datetime) -> str:
        """Serialize registration_time to ISO format."""
        return dt.isoformat()

    name: str | None = Field(default=None)
    club: str | None = Field(default=None)
    race: str | None = Field(default=None)
    race_id: UUID | None = Field(default=None)
    rank: int | None = Field(default=None)
    next_race: str | None = Field(default=None)
    next_race_id: UUID | None = Field(default=None)
    next_race_position: int | None = Field(default=None)
    status: str | None = Field(default=None)
    changelog: list[Changelog] | None = Field(default=None)
