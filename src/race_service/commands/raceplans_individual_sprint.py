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
TIME_BETWEEN_ROUNDS = timedelta(
    hours=00,
    minutes=10,
    seconds=00,
)
ROUNDS = ["Q", "S", "F"]
# ROUNDS = ["Q"]


async def calculate_raceplan_individual_sprint(
    event: dict,
    format_configuration: dict,
    raceclasses: List[dict],
) -> Raceplan:
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
    order = 1
    for round in ROUNDS:
        for raceclass in raceclasses_sorted:
            for heat in range(1, no_of_heats(raceclass, round) + 1):
                race = IndividualSprintRace(
                    raceclass=raceclass["name"],
                    order=order,
                    start_time=start_time,
                    no_of_contestants=no_of_contestants_in_heat(raceclass, round, heat),
                    round=round,
                    index=get_race_index(raceclass, round, heat),
                    heat=heat,
                )
                order += 1
                # Calculate start_time for next heat:
                start_time = start_time + TIME_BETWEEN_HEATS
                # Add the race to the raceplan:
                raceplan.races.append(race)
            # Calculate start_time for next round:
            start_time = start_time - TIME_BETWEEN_HEATS + TIME_BETWEEN_ROUNDS
            raceplan.no_of_contestants += raceclass["no_of_contestants"]
    raceplan.no_of_contestants = raceplan.no_of_contestants // len(ROUNDS)
    return raceplan


def no_of_heats(raceclass: dict, round: str) -> int:  # noqa: C901
    """Look up and calculate no_of_heats for raceclass."""
    _no_of_contestants = raceclass["no_of_contestants"]
    # TODO: find a way to not hard-code this table. It should be stored in race config.
    if 1 <= _no_of_contestants <= 7:
        if round == "Q":
            return 0
        elif round == "S":
            return 1
        elif round == "F":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 7 < _no_of_contestants <= 16:
        if round == "Q":
            return 0
        elif round == "S":
            return 2
        elif round == "F":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 16 < _no_of_contestants <= 24:
        if round == "Q":
            return 3
        elif round == "S":
            return 2
        elif round == "F":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 24 < _no_of_contestants <= 32:
        if round == "Q":
            return 4
        elif round == "S":
            return 2
        elif round == "F":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 32 < _no_of_contestants <= 40:
        if round == "Q":
            return 5
        elif round == "S":
            return 2
        elif round == "F":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 40 < _no_of_contestants <= 48:
        if round == "Q":
            return 6
        elif round == "S":
            return 2
        elif round == "F":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 48 < _no_of_contestants <= 56:
        if round == "Q":
            return 7
        elif round == "S":
            return 2
        elif round == "F":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 56 < _no_of_contestants <= MAX_OF_CONTESTANTS:
        if round == "Q":
            return 8
        elif round == "S":
            return 2
        elif round == "F":
            return 1
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    else:
        raise ValueError(
            f"Unsupported value for no of contestants: {_no_of_contestants}"
        )


def no_of_contestants_in_heat(raceclass: dict, round: str, heat: int) -> int:
    """Look up and calculate no_of_contestants in heat for raceclass."""
    # TODO: need to look up based on
    # - round,
    # - heat, and
    # - rules for how may contestants that qualify for next round.
    # TODO: need to smooth out no of contestants in heat. modulus and remainder
    no_of_contestants = no_of_contestants_qualified_to_round(raceclass, round)
    if round == "Q":
        quotient, remainder = divmod(no_of_contestants, no_of_heats(raceclass, round))
        if heat <= remainder:
            return quotient + 1
        else:
            return quotient
    elif round == "S":
        quotient, remainder = divmod(no_of_contestants, no_of_heats(raceclass, round))
        if heat <= remainder:
            return quotient + 1
        else:
            return quotient
    elif round == "F":
        quotient, remainder = divmod(no_of_contestants, no_of_heats(raceclass, round))
        if heat <= remainder:
            return quotient + 1
        else:
            return quotient
    else:
        raise ValueError(f"Unsupported value for round: {round}")


def no_of_contestants_qualified_to_round(  # noqa: C901
    raceclass: dict, round: str
) -> int:
    """Look up and calculate number of contestants qualified for next round."""
    _no_of_contestants = raceclass["no_of_contestants"]
    # TODO: find a way to not hard-code this table. It should be stored in race config.
    if 1 <= _no_of_contestants <= 7:
        if round == "Q":
            return _no_of_contestants
        elif round == "S":
            return _no_of_contestants // 2
        elif round == "F":
            return _no_of_contestants // 4
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 7 < _no_of_contestants <= 16:
        if round == "Q":
            return _no_of_contestants
        elif round == "S":
            return _no_of_contestants // 2
        elif round == "F":
            return _no_of_contestants // 4
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 16 < _no_of_contestants <= 24:
        if round == "Q":
            return _no_of_contestants
        elif round == "S":
            return _no_of_contestants // 2
        elif round == "F":
            return _no_of_contestants // 4
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 24 < _no_of_contestants <= 32:
        if round == "Q":
            return _no_of_contestants
        elif round == "S":
            return _no_of_contestants // 2
        elif round == "F":
            return _no_of_contestants // 4
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 32 < _no_of_contestants <= 40:
        if round == "Q":
            return _no_of_contestants
        elif round == "S":
            return _no_of_contestants // 2
        elif round == "F":
            return _no_of_contestants // 4
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 40 < _no_of_contestants <= 48:
        if round == "Q":
            return _no_of_contestants
        elif round == "S":
            return _no_of_contestants // 2
        elif round == "F":
            return _no_of_contestants // 4
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 48 < _no_of_contestants <= 56:
        if round == "Q":
            return _no_of_contestants
        elif round == "S":
            return _no_of_contestants // 2
        elif round == "F":
            return _no_of_contestants // 4
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 56 < _no_of_contestants <= MAX_OF_CONTESTANTS:
        if round == "Q":
            return _no_of_contestants
        elif round == "S":
            return _no_of_contestants // 2
        elif round == "F":
            return _no_of_contestants // 4
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    else:
        raise ValueError(
            f"Unsupported value for no of contestants: {_no_of_contestants}"
        )


def get_race_index(raceclass: dict, round: str, heat: int) -> str:  # noqa: C901
    """Find race index based on round and no_of_contestants."""
    if round == "Q":
        return ""
    _no_of_contestants = raceclass["no_of_contestants"]
    # TODO: find a way to not hard-code this table. It should be stored in race config.
    if 1 <= _no_of_contestants <= 7:
        if round == "S":
            return "A"
        elif round == "F":
            return "A"
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 7 < _no_of_contestants <= 16:
        if round == "S":
            return _no_of_contestants // 2
        elif round == "F":
            return "A"
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 16 < _no_of_contestants <= 24:
        if round == "S":
            return "A"
        elif round == "F":
            return "A"
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 24 < _no_of_contestants <= 32:
        if round == "S":
            return "A"
        elif round == "F":
            return "A"
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 32 < _no_of_contestants <= 40:
        if round == "S":
            return "A"
        elif round == "F":
            return "A"
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 40 < _no_of_contestants <= 48:
        if round == "S":
            return "A"
        elif round == "F":
            return "A"
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 48 < _no_of_contestants <= 56:
        if round == "S":
            return "A"
        elif round == "F":
            return "A"
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    elif 56 < _no_of_contestants <= MAX_OF_CONTESTANTS:
        if round == "S":
            return "A"
        elif round == "F":
            return "A"
        else:
            raise ValueError(f"Unsupported value for round: {round}")
    else:
        raise ValueError(
            f"Unsupported value for no of contestants: {_no_of_contestants}"
        )
