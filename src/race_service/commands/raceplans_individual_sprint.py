"""Module for raceplan commands."""
from datetime import date, datetime, time, timedelta
from typing import Any, List

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
            for heat in range(1, ConfigMatrix.no_of_heats(raceclass, round) + 1):
                race = IndividualSprintRace(
                    id="",
                    raceclass=raceclass["name"],
                    order=order,
                    start_time=start_time,
                    no_of_contestants=ConfigMatrix.no_of_contestants_in_heat(
                        raceclass, round, heat
                    ),
                    round=round,
                    index=ConfigMatrix.race_index(raceclass, round, heat),
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


class ConfigMatrix:
    """Class to represent the config matrix."""

    m: dict[int, dict[str, Any]] = {}
    m[1] = {
        "lim_no_contestants": 7,
        "no_of_heats_Q": 0,
        "no_of_heats_S": 1,
        "no_of_heats_F": 1,
        "race_index_Q": "",
        "race_index_S": "A",
        "race_index_F": "A",
        "no_of_contestants_qualified_to_Q": float("inf"),  # all
        "no_of_contestants_qualified_to_S": float("inf"),
        "no_of_contestants_qualified_to_F": float("inf"),
    }
    m[2] = {
        "lim_no_contestants": 16,
        "no_of_heats_Q": 0,
        "no_of_heats_S": 2,
        "no_of_heats_F": 1,
        "race_index_Q": "",
        "race_index_S": "A",
        "race_index_F": "A",
        "no_of_contestants_qualified_to_Q": float("inf"),  # all
        "no_of_contestants_qualified_to_S": float("inf"),
        "no_of_contestants_qualified_to_F": 4,
    }
    m[3] = {
        "lim_no_contestants": 24,
        "no_of_heats_Q": 3,
        "no_of_heats_S": 2,
        "no_of_heats_F": 1,
        "race_index_Q": "",
        "race_index_S": "A",
        "race_index_F": "A",
        "no_of_contestants_qualified_to_Q": float("inf"),  # all
        "no_of_contestants_qualified_to_S": 5,
        "no_of_contestants_qualified_to_F": 4,
    }
    m[4] = {
        "lim_no_contestants": 32,
        "no_of_heats_Q": 4,
        "no_of_heats_S": 2,
        "no_of_heats_F": 1,
        "race_index_Q": "",
        "race_index_S": "A",
        "race_index_F": "A",
        "no_of_contestants_qualified_to_Q": float("inf"),  # all
        "no_of_contestants_qualified_to_S": 4,
        "no_of_contestants_qualified_to_F": 4,
    }
    m[5] = {
        "lim_no_contestants": 40,
        "no_of_heats_Q": 5,
        "no_of_heats_S": 3,
        "no_of_heats_F": 1,
        "race_index_Q": "",
        "race_index_S": "A",
        "race_index_F": "A",
        "no_of_contestants_qualified_to_Q": float("inf"),  # all
        "no_of_contestants_qualified_to_S": 5,
        "no_of_contestants_qualified_to_F": 3,
    }
    m[6] = {
        "lim_no_contestants": 48,
        "no_of_heats_Q": 6,
        "no_of_heats_S": 3,
        "no_of_heats_F": 1,
        "race_index_Q": "",
        "race_index_S": "A",
        "race_index_F": "A",
        "no_of_contestants_qualified_to_Q": float("inf"),  # all
        "no_of_contestants_qualified_to_S": 4,
        "no_of_contestants_qualified_to_F": 3,
    }
    m[7] = {
        "lim_no_contestants": 56,
        "no_of_heats_Q": 7,
        "no_of_heats_S": 4,
        "no_of_heats_F": 1,
        "race_index_Q": "",
        "race_index_S": "A",
        "race_index_F": "A",
        "no_of_contestants_qualified_to_Q": float("inf"),  # all
        "no_of_contestants_qualified_to_S": 5,
        "no_of_contestants_qualified_to_F": 2,
    }
    m[8] = {
        "lim_no_contestants": MAX_OF_CONTESTANTS,
        "no_of_heats_Q": 8,
        "no_of_heats_S": 4,
        "no_of_heats_F": 1,
        "race_index_Q": "",
        "race_index_S": "A",
        "race_index_F": "A",
        "no_of_contestants_qualified_to_Q": float("inf"),  # all
        "no_of_contestants_qualified_to_S": 4,
        "no_of_contestants_qualified_to_F": 2,
    }

    @classmethod
    def no_of_heats(cls: Any, raceclass: dict, round: str) -> int:
        """Get no of heats."""
        no_of_contestants = raceclass["no_of_contestants"]
        _key = ConfigMatrix._get_key(no_of_contestants)
        if round == "Q":
            return ConfigMatrix.m[_key]["no_of_heats_Q"]
        elif round == "S":
            return ConfigMatrix.m[_key]["no_of_heats_S"]
        elif round == "F":
            return ConfigMatrix.m[_key]["no_of_heats_F"]
        else:
            raise ValueError(f"Unsupported value for round: {round}")

    @classmethod
    def race_index(cls: Any, raceclass: dict, round: str, heat: int) -> str:
        """Get race_index."""
        no_of_contestants = raceclass["no_of_contestants"]
        _key = ConfigMatrix._get_key(no_of_contestants)
        if round == "Q":
            return ConfigMatrix.m[_key]["race_index_Q"]
        elif round == "S":
            return ConfigMatrix.m[_key]["race_index_S"]
        elif round == "F":
            return ConfigMatrix.m[_key]["race_index_F"]
        else:
            raise ValueError(f"Unsupported value for round: {round}")

    @classmethod
    def no_of_contestants_in_heat(
        cls: Any, raceclass: dict, round: str, heat: int
    ) -> int:
        """Look up and calculate no_of_contestants in heat for raceclass."""
        no_of_contestants = raceclass["no_of_contestants"]
        _key = ConfigMatrix._get_key(no_of_contestants)
        if round == "Q":
            if (
                ConfigMatrix.m[_key]["no_of_contestants_qualified_to_Q"]
                > no_of_contestants
            ):
                _no = no_of_contestants
            else:
                _no = ConfigMatrix.m[_key]["no_of_contestants_qualified_to_Q"]

            quotient, remainder = divmod(
                _no, ConfigMatrix.no_of_heats(raceclass, round)
            )
            if heat <= remainder:
                return quotient + 1
            else:
                return quotient
        elif round == "S":
            _no = (
                ConfigMatrix.m[_key]["no_of_contestants_qualified_to_S"]
                * ConfigMatrix.m[_key]["no_of_heats_Q"]
            )

            quotient, remainder = divmod(
                _no, ConfigMatrix.no_of_heats(raceclass, round)
            )
            if heat <= remainder:
                return quotient + 1
            else:
                return quotient
        elif round == "F":
            _no = (
                ConfigMatrix.m[_key]["no_of_contestants_qualified_to_F"]
                * ConfigMatrix.m[_key]["no_of_heats_S"]
            )

            quotient, remainder = divmod(
                _no, ConfigMatrix.no_of_heats(raceclass, round)
            )
            if heat <= remainder:
                return quotient + 1
            else:
                return quotient
        else:
            raise ValueError(f"Unsupported value for round: {round}")

    @classmethod
    def _get_key(cls: Any, no_of_contestants: int) -> int:
        """Looks up key of matrix based on no_of_contestants."""
        if 1 <= no_of_contestants <= 7:
            return 1
        elif 7 < no_of_contestants <= 16:
            return 2
        elif 16 < no_of_contestants <= 24:
            return 3
        elif 24 < no_of_contestants <= 32:
            return 4
        elif 32 < no_of_contestants <= 40:
            return 5
        elif 40 < no_of_contestants <= 48:
            return 6
        elif 48 < no_of_contestants <= 56:
            return 7
        elif 56 < no_of_contestants <= MAX_OF_CONTESTANTS:
            return 8
        else:
            raise ValueError(
                f"Unsupported value for no of contestants: {no_of_contestants}"
            )
