"""Module for raceplan commands."""
from datetime import date, datetime, time, timedelta
from typing import Any, List, Tuple, Union

from race_service.models import IndividualSprintRace, Raceplan


async def calculate_raceplan_individual_sprint(
    event: dict,
    format_configuration: dict,
    raceclasses: List[dict],
) -> Tuple[Raceplan, List[IndividualSprintRace]]:
    """Calculate raceplan for Individual Sprint event."""
    raceplan = Raceplan(event_id=event["id"], races=list())
    races: List[IndividualSprintRace] = []
    # We get the number of contestants in plan from the raceclasses:
    raceplan.no_of_contestants = sum(
        raceclass["no_of_contestants"] for raceclass in raceclasses
    )
    # First we prepare the parameters:
    # get the time_between_groups as timedelta:
    TIME_BETWEEN_GROUPS = timedelta(
        hours=time.fromisoformat(format_configuration["time_between_groups"]).hour,
        minutes=time.fromisoformat(format_configuration["time_between_groups"]).minute,
        seconds=time.fromisoformat(format_configuration["time_between_groups"]).second,
    )
    TIME_BETWEEN_HEATS = timedelta(
        hours=time.fromisoformat(format_configuration["time_between_heats"]).hour,
        minutes=time.fromisoformat(format_configuration["time_between_heats"]).minute,
        seconds=time.fromisoformat(format_configuration["time_between_heats"]).second,
    )
    TIME_BETWEEN_ROUNDS = timedelta(
        hours=time.fromisoformat(format_configuration["time_between_rounds"]).hour,
        minutes=time.fromisoformat(format_configuration["time_between_rounds"]).minute,
        seconds=time.fromisoformat(format_configuration["time_between_rounds"]).second,
    )
    # get the first start_time from the event:
    start_time = datetime.combine(
        date.fromisoformat(event["date_of_event"]),
        time.fromisoformat(event["time_of_event"]),
    )

    # sort the raceclasses on order:
    raceclasses_sorted = sorted(raceclasses, key=lambda k: (k["group"], k["order"]))
    # We need to group the raceclasses by group:
    d: dict[int, list] = {}
    for raceclass in raceclasses_sorted:
        d.setdefault(raceclass["group"], []).append(raceclass)
    raceclasses_grouped = list(d.values())

    # Generate the races based on configuration and number of contestants
    order = 1
    for raceclasses in raceclasses_grouped:
        for round in ConfigMatrix.get_rounds():
            for raceclass in raceclasses:
                for index in reversed(ConfigMatrix.get_race_indexes(raceclass, round)):
                    for heat in range(
                        1, ConfigMatrix.get_no_of_heats(raceclass, round, index) + 1
                    ):
                        race = IndividualSprintRace(
                            id="",
                            order=order,
                            raceclass=raceclass["name"],
                            round=round,
                            index="" if round == "Q" else index,
                            heat=heat,
                            start_time=start_time,
                            no_of_contestants=0,
                            rule={}
                            if round == "F"
                            else ConfigMatrix.get_rule_from_to(raceclass, round, index),
                            event_id=event["id"],
                            raceplan_id="",
                            startlist_id="",
                        )
                        order += 1
                        # Calculate start_time for next heat:
                        start_time = start_time + TIME_BETWEEN_HEATS
                        # Add the race to the raceplan:
                        races.append(race)
                # Calculate start_time for next round:
                start_time = start_time - TIME_BETWEEN_HEATS + TIME_BETWEEN_ROUNDS
        # Calculate start_time for next group:
        start_time = start_time + TIME_BETWEEN_GROUPS

    # We need to calculate the number of contestants pr heat:
    for raceclasses in raceclasses_grouped:
        await _calculate_number_of_contestants_pr_race(raceclasses, raceplan, races)

    return raceplan, races


async def _calculate_number_of_contestants_pr_race(
    raceclasses: List[dict], raceplan: Raceplan, races: List[IndividualSprintRace]
) -> None:
    """Calculate number of contestants pr race based on plan."""
    for raceclass in raceclasses:
        await _calculate_number_of_contestants_pr_race_in_raceclass(
            raceclass, raceplan, races
        )


async def _calculate_number_of_contestants_pr_race_in_raceclass(  # noqa: C901
    raceclass: dict, raceplan: Raceplan, races: List[IndividualSprintRace]
) -> None:
    """Calculate number of contestants pr race pr raceclass based on plan."""
    no_of_Qs = len(
        [
            race
            for race in races
            if race.raceclass == raceclass["name"] and race.round == "Q"
        ]
    )
    no_of_SAs = len(
        [
            race
            for race in races
            if race.raceclass == raceclass["name"]
            and race.round == "S"
            and race.index == "A"
        ]
    )
    no_of_SCs = len(
        [
            race
            for race in races
            if race.raceclass == raceclass["name"]
            and race.round == "S"
            and race.index == "C"
        ]
    )
    no_of_FAs = len(
        [
            race
            for race in races
            if race.raceclass == raceclass["name"]
            and race.round == "F"
            and race.index == "A"
        ]
    )
    no_of_FBs = len(
        [
            race
            for race in races
            if race.raceclass == raceclass["name"]
            and race.round == "F"
            and race.index == "B"
        ]
    )
    no_of_FCs = len(
        [
            race
            for race in races
            if race.raceclass == raceclass["name"]
            and race.round == "F"
            and race.index == "C"
        ]
    )

    no_of_contestants_to_Qs = raceclass["no_of_contestants"]
    no_of_contestants_to_SAs = 0
    no_of_contestants_to_SCs = 0
    no_of_contestants_to_FAs = 0
    no_of_contestants_to_FBs = 0
    no_of_contestants_to_FCs = 0

    # Calculate number of contestants pr heat in Q:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"] and race.round == "Q"
    ]:
        # First we calculate no of cs in each Q race:
        # We need to "smooth" the contestants across the heats:
        quotient, remainder = divmod(
            no_of_contestants_to_Qs,
            no_of_Qs,
        )
        if race.heat <= remainder:
            race.no_of_contestants = quotient + 1
        else:
            race.no_of_contestants = quotient

    # Calculate number of contestants in SA, SC and FC:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"] and race.round == "Q"
    ]:
        # Then, for each race in round Q, some goes to SA:
        no_of_contestants_to_SAs += race.rule["S"]["A"]  # type: ignore
        # rest to SC:
        if race.rule["S"]["C"] != 0:
            no_of_contestants_to_SCs += race.no_of_contestants - race.rule["S"]["A"]  # type: ignore
        # or the rest may in some cases go directly to FC:
        if "F" in race.rule:
            if "C" in race.rule["F"]:
                no_of_contestants_to_FCs += race.no_of_contestants - race.rule["S"]["A"]  # type: ignore

    # Calculate number of contestants pr heat in SA:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"]
        and race.round == "S"
        and race.index == "A"
    ]:
        quotient, remainder = divmod(
            no_of_contestants_to_SAs,
            no_of_SAs,
        )
        if race.heat <= remainder:
            race.no_of_contestants = quotient + 1
        else:
            race.no_of_contestants = quotient

    # Calculate number of contestants pr heat in SC:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"]
        and race.round == "S"
        and race.index == "C"
    ]:
        quotient, remainder = divmod(
            no_of_contestants_to_SCs,
            no_of_SCs,
        )
        if race.heat <= remainder:
            race.no_of_contestants = quotient + 1
        else:
            race.no_of_contestants = quotient

    # Calculate number of contestants in FA and FB:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"]
        and race.round == "S"
        and race.index == "A"
    ]:
        no_of_contestants_to_FAs += race.rule["F"]["A"]  # type: ignore
        # rest to FB:
        if race.rule["F"]["B"] < float("inf"):
            no_of_contestants_to_FBs += race.rule["F"]["B"]  # type: ignore
        else:
            no_of_contestants_to_FBs += race.no_of_contestants - race.rule["F"]["A"]  # type: ignore

    # Calculate number of contestants in FC:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"]
        and race.round == "S"
        and race.index == "C"
    ]:
        no_of_contestants_to_FCs += race.rule["F"]["C"]  # type: ignore

    # Calculate number of contestants pr heat in FA:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"]
        and race.round == "F"
        and race.index == "A"
    ]:
        quotient, remainder = divmod(
            no_of_contestants_to_FAs,
            no_of_FAs,
        )
        if race.heat <= remainder:
            race.no_of_contestants = quotient + 1
        else:
            race.no_of_contestants = quotient

    # Calculate number of contestants pr heat in FB:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"]
        and race.round == "F"
        and race.index == "B"
    ]:
        quotient, remainder = divmod(
            no_of_contestants_to_FBs,
            no_of_FBs,
        )
        if race.heat <= remainder:
            race.no_of_contestants = quotient + 1
        else:
            race.no_of_contestants = quotient

    # Calculate number of contestants pr heat in FC:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"]
        and race.round == "F"
        and race.index == "C"
    ]:
        quotient, remainder = divmod(
            no_of_contestants_to_FCs,
            no_of_FCs,
        )
        if race.heat <= remainder:
            race.no_of_contestants = quotient + 1
        else:
            race.no_of_contestants = quotient


class ConfigMatrix:
    """Class to represent the config matrix."""

    ROUNDS = ["Q", "S", "F"]

    MAX_NO_OF_CONTESTANTS = 80  # TODO: Get this from competition-format
    ALL = 10
    REST = float("inf")
    m: dict[int, dict[str, Any]] = {}
    m[1] = {
        "lim_no_contestants": 7,
        "no_of_heats": {
            "Q": {"A": 0},
            "S": {"A": 1, "C": 0},
            "F": {"A": 1, "B": 0, "C": 0},
        },
        "from_to": {
            "Q": {"A": {"S": {"A": ALL, "C": 0}}},
            "S": {"A": {"F": {"A": ALL, "B": 0}}, "C": {"F": {"C": 0}}},
        },
    }
    m[2] = {
        "lim_no_contestants": 16,
        "no_of_heats": {
            "Q": {"A": 0},
            "S": {"A": 2, "C": 0},
            "F": {"A": 1, "B": 1, "C": 0},
        },
        "from_to": {
            "Q": {"A": {"S": {"A": ALL, "C": 0}}},
            "S": {"A": {"F": {"A": 4, "B": REST}}, "C": {"F": {"C": 0}}},
        },
    }
    m[3] = {
        "lim_no_contestants": 24,
        "no_of_heats": {
            "Q": {"A": 3},
            "S": {"A": 2, "C": 0},
            "F": {"A": 1, "B": 1, "C": 1},
        },
        "from_to": {
            "Q": {"A": {"S": {"A": 5, "C": 0}, "F": {"C": REST}}},
            "S": {"A": {"F": {"A": 4, "B": REST}}, "C": {"F": {"C": 0}}},
        },
    }
    m[4] = {
        "lim_no_contestants": 32,
        "no_of_heats": {
            "Q": {"A": 4},
            "S": {"A": 2, "C": 2},
            "F": {"A": 1, "B": 1, "C": 1},
        },
        "from_to": {
            "Q": {"A": {"S": {"A": 4, "C": REST}}},
            "S": {"A": {"F": {"A": 4, "B": REST}}, "C": {"F": {"C": 4}}},
        },
    }
    m[5] = {
        "lim_no_contestants": 40,
        "no_of_heats": {
            "Q": {"A": 5},
            "S": {"A": 3, "C": 2},
            "F": {"A": 1, "B": 1, "C": 1},
        },
        "from_to": {
            "Q": {"A": {"S": {"A": 5, "C": REST}}},
            "S": {"A": {"F": {"A": 3, "B": 3}}, "C": {"F": {"C": 4}}},
        },
    }
    m[6] = {
        "lim_no_contestants": 48,
        "no_of_heats": {
            "Q": {"A": 6},
            "S": {"A": 3, "C": 3},
            "F": {"A": 1, "B": 1, "C": 1},
        },
        "from_to": {
            "Q": {"A": {"S": {"A": 4, "C": REST}}},
            "S": {"A": {"F": {"A": 3, "B": 3}}, "C": {"F": {"C": 3}}},
        },
    }
    m[7] = {
        "lim_no_contestants": 56,
        "no_of_heats": {
            "Q": {"A": 7},
            "S": {"A": 4, "C": 3},
            "F": {"A": 1, "B": 1, "C": 1},
        },
        "from_to": {
            "Q": {"A": {"S": {"A": 5, "C": REST}}},
            "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 3}}},
        },
    }
    m[8] = {
        "lim_no_contestants": MAX_NO_OF_CONTESTANTS,
        "no_of_heats": {
            "Q": {"A": 8},
            "S": {"A": 4, "C": 4},
            "F": {"A": 1, "B": 1, "C": 1},
        },
        "from_to": {
            "Q": {"A": {"S": {"A": 4, "C": REST}}},
            "S": {"A": {"F": {"A": 2, "B": 2}}, "C": {"F": {"C": 2}}},
        },
    }

    @classmethod
    def get_rounds(cls: Any) -> list:
        """Get no of heats pr round and index."""
        return ConfigMatrix.ROUNDS

    @classmethod
    def get_no_of_heats(cls: Any, raceclass: dict, round: str, index: str) -> int:
        """Get no of heats pr round and index."""
        _key = ConfigMatrix._get_key(raceclass["no_of_contestants"])
        return ConfigMatrix.m[_key]["no_of_heats"][round][index]

    @classmethod
    def get_race_indexes(cls: Any, raceclass: dict, round: str) -> list:
        """Get race indexes pr round."""
        _key = ConfigMatrix._get_key(raceclass["no_of_contestants"])
        return [key for key in ConfigMatrix.m[_key]["no_of_heats"][round]]

    @classmethod
    def get_rule_from_to(
        cls: Any,
        raceclass: dict,
        from_round: str,
        from_index: str,
    ) -> dict[str, dict[str, Union[int, float]]]:
        """Get race rule pr round and index."""
        _key = ConfigMatrix._get_key(raceclass["no_of_contestants"])
        return ConfigMatrix.m[_key]["from_to"][from_round][from_index]

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
        elif 56 < no_of_contestants <= ConfigMatrix.MAX_NO_OF_CONTESTANTS:
            return 8
        else:
            raise ValueError(
                f"Unsupported value for no of contestants: {no_of_contestants}"
            )
