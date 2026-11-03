"""Startlist model module."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_serializer

from .changelog import Changelog


class StartEntry(BaseModel):
    """Model with details about a start-entry."""

    id: UUID = Field(default_factory=uuid4)
    startlist_id: UUID
    race_id: UUID
    bib: int
    starting_position: int
    scheduled_start_time: datetime

    @field_serializer("scheduled_start_time")
    def serialize_scheduled_start_time(self, dt: datetime) -> str:
        """Serialize scheduled_start_time to ISO format."""
        return dt.isoformat()

    name: str
    club: str
    status: str | None = Field(default=None)
    changelog: list[Changelog] | None = Field(default=None)


class Startlist(BaseModel):
    """Model with details about a startlist."""

    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    no_of_contestants: int
    start_entries: list[UUID]
