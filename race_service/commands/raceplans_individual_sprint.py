"""Module for raceplan commands."""
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Tuple, Union

from race_service.models import IndividualSprintRace, Raceplan


async def calculate_raceplan_individual_sprint(  # noqa: C901
    event: dict,
    competition_format: dict,
    raceclasses: List[dict],
) -> Tuple[Raceplan, List[IndividualSprintRace]]:
    """Calculate raceplan for Individual Sprint event."""
    # Initialize
    raceplan = Raceplan(event_id=event["id"], races=list())
    races: List[IndividualSprintRace] = []

    # We get the number of contestants in plan from the raceclasses:
    raceplan.no_of_contestants = sum(
        raceclass["no_of_contestants"] for raceclass in raceclasses
    )
    # First we prepare the parameters:
    # get the time_between_groups as timedelta:
    TIME_BETWEEN_GROUPS = timedelta(
        hours=time.fromisoformat(competition_format["time_between_groups"]).hour,
        minutes=time.fromisoformat(competition_format["time_between_groups"]).minute,
        seconds=time.fromisoformat(competition_format["time_between_groups"]).second,
    )
    TIME_BETWEEN_HEATS = timedelta(
        hours=time.fromisoformat(competition_format["time_between_heats"]).hour,
        minutes=time.fromisoformat(competition_format["time_between_heats"]).minute,
        seconds=time.fromisoformat(competition_format["time_between_heats"]).second,
    )
    TIME_BETWEEN_ROUNDS = timedelta(
        hours=time.fromisoformat(competition_format["time_between_rounds"]).hour,
        minutes=time.fromisoformat(competition_format["time_between_rounds"]).minute,
        seconds=time.fromisoformat(competition_format["time_between_rounds"]).second,
    )
    # get the first start_time from the event:
    start_time = datetime.combine(
        date.fromisoformat(event["date_of_event"]),
        time.fromisoformat(event["time_of_event"]),
    )

    # Sort the raceclasses on group and order:
    raceclasses_sorted = sorted(raceclasses, key=lambda k: (k["group"], k["order"]))
    # We need to group the raceclasses by group:
    d: Dict[int, list] = {}
    for raceclass in raceclasses_sorted:
        d.setdefault(raceclass["group"], []).append(raceclass)
    raceclasses_grouped = list(d.values())

    # Generate the races, group by group, based on competition-format and number of contestants
    order = 1
    for raceclasses in raceclasses_grouped:
        # Initalize ConfigMatrix pr group:
        ConfigMatrix.initialize(competition_format, raceclasses)
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
                            index="" if round in ["Q", "R1", "R2"] else index,
                            heat=heat,
                            start_time=start_time,
                            max_no_of_contestants=competition_format[
                                "max_no_of_contestants_in_race"
                            ],
                            no_of_contestants=0,
                            rule={}
                            if round in ["F", "R2"]
                            else ConfigMatrix.get_rule_from_to(raceclass, round, index),
                            event_id=event["id"],
                            raceplan_id="",
                            start_entries=[],
                            results={},
                        )
                        order += 1
                        # Calculate start_time for next heat:
                        start_time = start_time + TIME_BETWEEN_HEATS
                        # Add the race to the raceplan:
                        races.append(race)
            # Calculate start_time for next round:
            if round in ConfigMatrix.get_rounds_in_raceclass(raceclass):
                start_time = start_time - TIME_BETWEEN_HEATS + TIME_BETWEEN_ROUNDS
        # Calculate start_time for next group:
        start_time = start_time + TIME_BETWEEN_GROUPS

    # We need to calculate the number of contestants pr race:
    for raceclasses in raceclasses_grouped:
        for raceclass in raceclasses:
            if raceclass["ranking"]:
                await _calculate_number_of_contestants_pr_race_in_raceclass_ranked(
                    raceclass, races
                )
            else:
                await _calculate_number_of_contestants_pr_race_in_raceclass_non_ranked(
                    raceclass, races
                )

    return raceplan, races


async def _calculate_number_of_contestants_pr_race_in_raceclass_ranked(  # noqa: C901
    raceclass: dict, races: List[IndividualSprintRace]
) -> None:
    """Calculate number of contestants pr race in given raceclass."""
    no_of_contestants_to_Qs = raceclass["no_of_contestants"]
    no_of_contestants_to_SAs = 0
    no_of_contestants_to_SCs = 0
    no_of_contestants_to_FAs = 0
    no_of_contestants_to_FBs = 0
    no_of_contestants_to_FCs = 0

    # Calculate number of contestants pr heat in Q and store in race:
    await _calculate_number_of_contestants_pr_heat_in_round(
        round="Q",
        index="",
        no_of_contestants_to_round=no_of_contestants_to_Qs,
        races=races,
        raceclass=raceclass,
    )

    # TODO: Figure out if there is a way to make a more generic function for this:
    # If there is to be a round "S" or "F", calculate number of contestants in SA, SC and FC:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"] and race.round == "Q"
    ]:
        if "S" in race.rule:
            # Then, for each race in round Q, some goes to SA:
            no_of_contestants_to_SAs += race.rule["S"]["A"]  # type: ignore
            # rest to SC:
            if race.rule["S"]["C"] != 0:
                no_of_contestants_to_SCs += race.no_of_contestants - race.rule["S"]["A"]  # type: ignore
            # or the rest may in some cases go directly to FC:
        if "F" in race.rule:
            if "C" in race.rule["F"]:
                no_of_contestants_to_FCs += race.no_of_contestants - race.rule["S"]["A"]  # type: ignore
            if "A" in race.rule["F"]:
                if race.rule["F"]["A"] == "ALL":
                    no_of_contestants_to_FAs = race.no_of_contestants
                else:
                    no_of_contestants_to_FAs += race.rule["F"]["A"]  # type: ignore
            # rest to FB:
            if "B" in race.rule["F"]:
                if race.rule["F"]["B"] == "REST":
                    no_of_contestants_to_FBs += race.no_of_contestants - race.rule["F"]["A"]  # type: ignore
                else:
                    no_of_contestants_to_FBs += race.rule["F"]["B"]  # type: ignore

    # Calculate number of contestants pr heat in SA:
    await _calculate_number_of_contestants_pr_heat_in_round(
        round="S",
        index="A",
        no_of_contestants_to_round=no_of_contestants_to_SAs,
        races=races,
        raceclass=raceclass,
    )
    # Calculate number of contestants pr heat in SC:
    # Calculate number of contestants pr heat in SA:
    await _calculate_number_of_contestants_pr_heat_in_round(
        round="S",
        index="C",
        no_of_contestants_to_round=no_of_contestants_to_SCs,
        races=races,
        raceclass=raceclass,
    )

    # Calculate number of contestants in FA, FB and FC:
    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"] and race.round == "S"
    ]:
        if "F" in race.rule:
            if "A" in race.rule["F"]:
                no_of_contestants_to_FAs += race.rule["F"]["A"]  # type: ignore
            if "B" in race.rule["F"]:
                if race.rule["F"]["B"] == "REST":
                    no_of_contestants_to_FBs += race.no_of_contestants - race.rule["F"]["A"]  # type: ignore
                else:
                    no_of_contestants_to_FBs += race.rule["F"]["B"]  # type: ignore
            if "C" in race.rule["F"]:
                no_of_contestants_to_FCs += race.rule["F"]["C"]  # type: ignore

    # Calculate number of contestants pr heat in FA:
    await _calculate_number_of_contestants_pr_heat_in_round(
        round="F",
        index="A",
        no_of_contestants_to_round=no_of_contestants_to_FAs,
        races=races,
        raceclass=raceclass,
    )

    # Calculate number of contestants pr heat in FB:
    await _calculate_number_of_contestants_pr_heat_in_round(
        round="F",
        index="B",
        no_of_contestants_to_round=no_of_contestants_to_FBs,
        races=races,
        raceclass=raceclass,
    )

    # Calculate number of contestants pr heat in FC:
    await _calculate_number_of_contestants_pr_heat_in_round(
        round="F",
        index="C",
        no_of_contestants_to_round=no_of_contestants_to_FCs,
        races=races,
        raceclass=raceclass,
    )


async def _calculate_number_of_contestants_pr_race_in_raceclass_non_ranked(  # noqa: C901
    raceclass: dict, races: List[IndividualSprintRace]
) -> None:
    """Calculate number of contestants pr race in given raceclass and store in race."""
    # Calculate number of contestants pr heat in R1:
    await _calculate_number_of_contestants_pr_heat_in_round(
        round="R1",
        index="",
        no_of_contestants_to_round=raceclass["no_of_contestants"],
        races=races,
        raceclass=raceclass,
    )

    # Calculate number of contestants pr heat in R2:
    await _calculate_number_of_contestants_pr_heat_in_round(
        round="R2",
        index="",
        no_of_contestants_to_round=raceclass["no_of_contestants"],
        races=races,
        raceclass=raceclass,
    )


async def _calculate_number_of_contestants_pr_heat_in_round(
    raceclass: Dict,
    round: str,
    index: str,
    no_of_contestants_to_round: int,
    races: List[IndividualSprintRace],
) -> None:
    # Calculate number of contestants pr heat in round:

    no_of_races_in_round = len(
        [
            race
            for race in races
            if race.raceclass == raceclass["name"]
            and race.round == round
            and race.index == index
        ]
    )

    for race in [
        race
        for race in races
        if race.raceclass == raceclass["name"]
        and race.round == round
        and race.index == index
    ]:
        # We need to "smooth" the contestants across the heats:
        quotient, remainder = divmod(
            no_of_contestants_to_round,
            no_of_races_in_round,
        )
        if race.heat <= remainder:
            race.no_of_contestants = quotient + 1
        else:
            race.no_of_contestants = quotient


class ConfigMatrix:
    """Class to represent the config matrix."""

    ROUNDS: List[str] = []
    RANKING: bool = True
    MAX_NO_OF_CONTESTANTS_IN_RACECLASS: int
    MAX_NO_OF_CONTESTANTS_IN_RACE: int
    m: List[Dict[str, Any]] = []

    @classmethod
    def initialize(
        cls: Any, competition_format: Dict, raceclasses_in_group: List[Dict]
    ) -> None:
        """Initalize parameters based on competition-format and raceclasses in group."""
        if raceclasses_in_group[0]["ranking"]:
            ConfigMatrix.RANKING = True
        else:
            ConfigMatrix.RANKING = False

        if ConfigMatrix.RANKING:
            ConfigMatrix.ROUNDS = competition_format["rounds_ranked_classes"]
        else:
            ConfigMatrix.ROUNDS = competition_format["rounds_non_ranked_classes"]

        ConfigMatrix.MAX_NO_OF_CONTESTANTS_IN_RACECLASS = competition_format[
            "max_no_of_contestants_in_raceclass"
        ]
        ConfigMatrix.MAX_NO_OF_CONTESTANTS_IN_RACE = competition_format[
            "max_no_of_contestants_in_race"
        ]

        # Initialize matrix
        if ConfigMatrix.RANKING:
            # ConfigMatrix for ranked raceclasses:
            ConfigMatrix.m = competition_format["race_config_ranked"]
        else:
            # ConfigMatrix for non ranked raceclasses:
            ConfigMatrix.m = competition_format["race_config_non_ranked"]

    @classmethod
    def get_rounds(cls: Any) -> list:
        """Get default rounds."""
        return ConfigMatrix.ROUNDS

    @classmethod
    def get_rounds_in_raceclass(cls: Any, raceclass: dict) -> list:
        """Get actual rounds in raceclass."""
        _key = ConfigMatrix._get_index(raceclass["no_of_contestants"])
        return ConfigMatrix.m[_key]["rounds"]

    @classmethod
    def get_no_of_heats(cls: Any, raceclass: dict, round: str, index: str) -> int:
        """Get no of heats pr round and index."""
        _key = ConfigMatrix._get_index(raceclass["no_of_contestants"])
        return ConfigMatrix.m[_key]["no_of_heats"][round][index]

    @classmethod
    def get_race_indexes(cls: Any, raceclass: dict, round: str) -> list:
        """Get race indexes pr round."""
        _key = ConfigMatrix._get_index(raceclass["no_of_contestants"])
        if round not in ConfigMatrix.m[_key]["no_of_heats"]:
            return []
        return [key for key in ConfigMatrix.m[_key]["no_of_heats"][round]]

    @classmethod
    def get_rule_from_to(
        cls: Any,
        raceclass: dict,
        from_round: str,
        from_index: str,
    ) -> Dict[str, Dict[str, Union[int, str]]]:
        """Get race rule pr round and index."""
        _key = ConfigMatrix._get_index(raceclass["no_of_contestants"])
        return ConfigMatrix.m[_key]["from_to"][from_round][from_index]

    @classmethod
    def _get_index(cls: Any, no_of_contestants: int) -> int:
        """Find index of correct matrix in list based on no_of_contestants."""
        _index = next(
            (
                index
                for (index, d) in enumerate(ConfigMatrix.m)
                if no_of_contestants <= d["max_no_of_contestants"]
            ),
            None,
        )
        if _index is None:
            raise ValueError(
                f"Unsupported value for no of contestants: {no_of_contestants}"
            )
        return _index
