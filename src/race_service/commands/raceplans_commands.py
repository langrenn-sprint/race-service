"""Module for contestants service."""
from typing import Any

from race_service.models import Raceplan
from race_service.services import (
    RaceplansService,
)


class RaceplansCommands:
    """Class representing a commands on events."""

    @classmethod
    async def generate_raceplan_for_event(cls: Any, db: Any, event: dict) -> str:
        """Generate raceplan for event function."""
        # Create a raceplan object:
        raceplan = Raceplan(event_id=event["event_id"], races=list())
        raceplan_id = await RaceplansService.create_raceplan(db, raceplan)
        assert raceplan_id
        return raceplan_id
