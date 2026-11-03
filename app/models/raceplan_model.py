"""Raceplan model module."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Raceplan(BaseModel):
    """Model with details about a raceplan."""

    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    races: list[UUID]  # ids to every race in this plan
    no_of_contestants: int = 0
