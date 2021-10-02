"""Module for raceplan commands."""
from datetime import date, datetime, time, timedelta
from typing import List

from race_service.models import Race, Raceplan
from race_service.services import create_id


async def calculate_raceplan_interval_start(
    event: dict,
    format_configuration: dict,
    raceclasses: List[dict],
) -> Raceplan:
    """Calculate raceplan for Interval Start event."""
    raceplan = Raceplan(event_id=event["id"], races=list())
    # sort the raceclasses on order:
    raceclasses_sorted = sorted(raceclasses, key=lambda k: k["order"])
    # get the interval as timedelta:
    intervals = timedelta(
        hours=time.fromisoformat(format_configuration["intervals"]).hour,
        minutes=time.fromisoformat(format_configuration["intervals"]).minute,
        seconds=time.fromisoformat(format_configuration["intervals"]).second,
    )
    # get the first start_time from the event:
    start_time = datetime.combine(
        date.fromisoformat(event["date_of_event"]),
        time.fromisoformat(event["time_of_event"]),
    )

    for raceclass in raceclasses_sorted:
        race = Race(
            id=create_id(),
            raceclass=raceclass["name"],
            order=raceclass["order"],
            start_time=start_time,
            no_of_contestants=raceclass["no_of_contestants"],
        )
        # Calculate start_time for next raceclass:
        start_time = start_time + intervals * raceclass["no_of_contestants"]
        # Add the race to the raceplan:
        raceplan.races.append(race)
        raceplan.no_of_contestants += race.no_of_contestants
    return raceplan
