"""Module for raceplan commands."""
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Tuple

from race_service.models import IntervalStartRace, Raceplan


async def calculate_raceplan_interval_start(
    event: dict,
    competition_format: dict,
    raceclasses: List[dict],
) -> Tuple[Raceplan, List[IntervalStartRace]]:
    """Calculate raceplan for Interval Start event."""
    raceplan = Raceplan(event_id=event["id"], races=list())
    races: List[IntervalStartRace] = []
    # get the time_between_groups as timedelta:
    time_between_groups = timedelta(
        hours=time.fromisoformat(competition_format["time_between_groups"]).hour,
        minutes=time.fromisoformat(competition_format["time_between_groups"]).minute,
        seconds=time.fromisoformat(competition_format["time_between_groups"]).second,
    )
    # get the interval as timedelta:
    intervals = timedelta(
        hours=time.fromisoformat(competition_format["intervals"]).hour,
        minutes=time.fromisoformat(competition_format["intervals"]).minute,
        seconds=time.fromisoformat(competition_format["intervals"]).second,
    )
    # get the first start_time from the event:
    start_time = datetime.combine(
        date.fromisoformat(event["date_of_event"]),
        time.fromisoformat(event["time_of_event"]),
    )

    # sort the raceclasses on group and order:
    raceclasses_sorted = sorted(raceclasses, key=lambda k: (k["group"], k["order"]))
    # We need to group the raceclasses by group:
    d: Dict[int, list] = {}
    for raceclass in raceclasses_sorted:
        d.setdefault(raceclass["group"], []).append(raceclass)
    raceclasses_grouped = list(d.values())

    order = 1
    no_of_contestants = 0
    for raceclasses in raceclasses_grouped:
        for raceclass in raceclasses:
            race = IntervalStartRace(
                id="",
                raceclass=raceclass["name"],
                order=order,
                start_time=start_time,
                max_no_of_contestants=competition_format[
                    "max_no_of_contestants_in_race"
                ],
                no_of_contestants=raceclass["no_of_contestants"],
                event_id=event["id"],
                raceplan_id="",
                start_entries=[],
                results={},
            )
            # Calculate start_time for next raceclass:
            start_time = start_time + intervals * raceclass["no_of_contestants"]
            # Add the race to the raceplan:
            races.append(race)
            no_of_contestants += race.no_of_contestants
            order += 1
        start_time = start_time + time_between_groups
    raceplan.no_of_contestants = no_of_contestants

    return raceplan, races
