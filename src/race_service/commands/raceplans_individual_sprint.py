"""Module for raceplan commands."""
from datetime import date, datetime, time
from typing import List

from race_service.models import Race, Raceplan


async def calculate_raceplan_individual_sprint(
    event: dict,
    format_configuration: dict,
    raceclasses: List[dict],
) -> Raceplan:  # pragma: no cover
    """Calculate raceplan for Individual Sprint event."""
    raceplan = Raceplan(event_id=event["id"], races=list())
    # sort the raceclasses on order:
    raceclasses_sorted = sorted(raceclasses, key=lambda k: k["order"])
    # get the first start_time from the event:
    start_time = datetime.combine(
        date.fromisoformat(event["date_of_event"]),
        time.fromisoformat(event["time_of_event"]),
    )

    for raceclass in raceclasses_sorted:
        race = Race(
            raceclass=raceclass["name"],
            order=raceclass["order"],
            start_time=start_time,
            no_of_contestants=raceclass["no_of_contestants"],
        )
        # Calculate start_time for next raceclass:
        start_time = start_time + raceclass["no_of_contestants"]
        # Add the race to the raceplan:
        raceplan.races.append(race)
        raceplan.no_of_contestants += race.no_of_contestants
    return raceplan
