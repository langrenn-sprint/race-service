"""Race model module."""

from datetime import datetime
from enum import IntEnum
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_serializer


class RaceResultStatus(IntEnum):
    """Valid values for a raceresult status."""

    NONE = 0
    UNOFFICIAL = 1
    OFFICIAL = 2


class RaceResult(BaseModel):
    """Model with details about a race-result."""

    id: UUID = Field(default_factory=uuid4)
    race_id: UUID
    timing_point: str
    no_of_contestants: int
    ranking_sequence: list[UUID]  # list of references to TimeEvent
    status: int  # int with reference to RaceResultStatus


class Race(BaseModel):
    """Model with details about a race."""

    id: UUID = Field(default_factory=uuid4)
    raceclass: str
    order: int
    start_time: datetime

    @field_serializer("start_time")
    def serialize_start_time(self, dt: datetime) -> str:
        """Serialize start_time to ISO format."""
        return dt.isoformat()

    max_no_of_contestants: int
    no_of_contestants: int
    event_id: UUID
    raceplan_id: UUID
    start_entries: list[UUID]  # list of references to StartEntry
    results: dict[str, UUID]  # dict with reference to RaceResult pr timing point


class IntervalStartRace(Race):
    """Model with details about an interval start race."""

    datatype: Literal["interval_start"] = "interval_start"


class IndividualSprintRace(Race):
    """Model with details about an individual sprint race."""

    round: str = ""
    index: str = ""
    heat: int = 0
    rule: dict[str, dict[str, int | str]] = Field(default_factory=dict)
    datatype: Literal["individual_sprint"] = "individual_sprint"


RaceUnion = Annotated[
    IndividualSprintRace | IntervalStartRace, Field(discriminator="datatype")
]
