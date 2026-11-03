"""Changelog model module."""

from datetime import datetime

from pydantic import BaseModel, field_serializer


class Changelog(BaseModel):
    """Model representing a changelog."""

    timestamp: datetime

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime) -> str:
        """Serialize timestamp to ISO format."""
        return dt.isoformat()

    user_id: str
    comment: str
