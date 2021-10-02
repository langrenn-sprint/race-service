"""Module for raceplan commands."""
from datetime import date, datetime, time, timedelta
from typing import List

from race_service.models import IndividualSprintRace, Raceplan

MAX_OF_CONTESTANTS = 80
TIME_BETWEEN_HEATS = timedelta(
    hours=00,
    minutes=2,
    seconds=30,
)
ROUNDS = ["Quarterfinals", "Semi-finals", "Finals"]
# ROUNDS = ["Quarterfinals"]


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

    # Generate the races based on configuration and number of contestants
    # for round in ROUNDS:
    for round in ROUNDS:
        order = 1
        for raceclass in raceclasses_sorted:
            for heat in range(0, no_of_heats(raceclass, round)):
                race = IndividualSprintRace(
                    raceclass=raceclass["name"],
                    order=order,
                    start_time=start_time,
                    no_of_contestants=no_of_contestants_in_heat(raceclass, round),
                    round=round,
                    heat=heat + 1,
                )
                order += 1
                # Calculate start_time for next heat:
                start_time = start_time + TIME_BETWEEN_HEATS
                # Add the race to the raceplan:
                raceplan.races.append(race)
            raceplan.no_of_contestants += raceclass["no_of_contestants"]
    raceplan.no_of_contestants = raceplan.no_of_contestants // len(ROUNDS)
    return raceplan


def no_of_heats(raceclass: dict, round: str) -> int:  # noqa: C901
    """Look up and calculate no_of_heats for raceclass."""
    _no_of_contestants = raceclass["no_of_contestants"]
    # TODO: find a way to not hard-code this table. It should be stored in race config.
    if 1 <= _no_of_contestants <= 7:
        if round == "Quarterfinals":
            return 0
        elif round == "Semi-finals":
            return 1
        elif round == "Finals":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 7 < _no_of_contestants <= 16:
        if round == "Quarterfinals":
            return 0
        elif round == "Semi-finals":
            return 2
        elif round == "Finals":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 16 < _no_of_contestants <= 24:
        if round == "Quarterfinals":
            return 3
        elif round == "Semi-finals":
            return 2
        elif round == "Finals":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 24 < _no_of_contestants <= 32:
        if round == "Quarterfinals":
            return 4
        elif round == "Semi-finals":
            return 2
        elif round == "Finals":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 32 < _no_of_contestants <= 40:
        if round == "Quarterfinals":
            return 5
        elif round == "Semi-finals":
            return 2
        elif round == "Finals":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 40 < _no_of_contestants <= 48:
        if round == "Quarterfinals":
            return 6
        elif round == "Semi-finals":
            return 2
        elif round == "Finals":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 48 < _no_of_contestants <= 56:
        if round == "Quarterfinals":
            return 7
        elif round == "Semi-finals":
            return 2
        elif round == "Finals":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 56 < _no_of_contestants <= MAX_OF_CONTESTANTS:
        if round == "Quarterfinals":
            return 8
        elif round == "Semi-finals":
            return 2
        elif round == "Finals":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    else:
        raise ValueError(
            f"Unsupported value for no of contestants: {_no_of_contestants}"
        )


def no_of_contestants_in_heat(raceclass: dict, round: str) -> int:  # pragma: no cover
    """Look up and calculate no_of_contestants in heat for raceclass."""
    # TODO: need to look up based on round and
    # rules for how may contestants that qualify for next round.
    # TODO: need to smooth out no of contestants in heat.
    return raceclass["no_of_contestants"] // no_of_heats(raceclass, round)
