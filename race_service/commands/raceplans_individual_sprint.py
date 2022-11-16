"""Module for raceplan commands."""
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Tuple, Union

from race_service.models import IndividualSprintRace, Raceplan
from .exceptions import IllegalValueInRaceError


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
                            index=index,
                            heat=heat,
                            start_time=start_time,
                            max_no_of_contestants=competition_format[
                                "max_no_of_contestants_in_race"
                            ],
                            no_of_contestants=0,
                            rule=ConfigMatrix.get_rule_from_to(raceclass, round, index),
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
        ConfigMatrix.initialize(competition_format, raceclasses)
        for raceclass in raceclasses:
            await _calculate_number_of_contestants_pr_race_in_raceclass(
                raceclass, races
            )

    return raceplan, races


async def _calculate_number_of_contestants_pr_race_in_raceclass(  # noqa: C901
    raceclass: dict, races: List[IndividualSprintRace]
) -> None:
    """Calculate number of contestants pr race in given raceclass and store in race."""
    rounds: List[str] = ConfigMatrix.get_rounds_in_raceclass(raceclass)

    # Initialize number of contestants pr round/index:
    no_of_contestants: Dict[str, Dict[str, int]] = {}
    for round in rounds:
        no_of_contestants[round] = {}
        for index in ConfigMatrix.get_race_indexes(raceclass, round):
            no_of_contestants[round][index] = 0

    # Calculate number of contestants in first round:
    no_of_contestants[rounds[0]][
        ConfigMatrix.get_race_indexes(raceclass, round)[0]
    ] = raceclass["no_of_contestants"]

    # Calculate number of contestants pr race in round/index:
    for round in rounds:
        for index in ConfigMatrix.get_race_indexes(raceclass, round):
            await _set_number_of_contestants_in_race(
                round=round,
                index=index,
                no_of_contestants=no_of_contestants[round][index],
                races=races,
                raceclass=raceclass,
            )

        # Based on rules (from_to) in each race in this round, calculate number of contestants
        # to next round by summing up:
        for race in [
            race
            for race in races
            if race.raceclass == raceclass["name"] and race.round == round
        ]:
            _no_of_contestants_left_in_race = race.no_of_contestants
            for _round in race.rule.keys():
                for _index in race.rule[_round]:
                    if race.rule[_round][_index] == "ALL":
                        no_of_contestants[_round][
                            _index
                        ] += _no_of_contestants_left_in_race
                        _no_of_contestants_left_in_race -= no_of_contestants[_round][
                            _index
                        ]
                    elif race.rule[_round][_index] == "REST":
                        no_of_contestants[_round][
                            _index
                        ] += _no_of_contestants_left_in_race
                        _no_of_contestants_left_in_race -= no_of_contestants[_round][
                            _index
                        ]
                    elif type(race.rule[_round][_index]) is int:
                        if (
                            int(race.rule[_round][_index])
                            > _no_of_contestants_left_in_race
                        ):
                            no_of_contestants[_round][
                                _index
                            ] += _no_of_contestants_left_in_race

                        else:
                            no_of_contestants[_round][_index] += int(
                                race.rule[_round][_index]
                            )
                            _no_of_contestants_left_in_race -= int(
                                race.rule[_round][_index]
                            )
                    else:
                        raise IllegalValueInRaceError(
                            f"Unknown rule: {race.rule[_round][_index]}"
                        )  # pragma: no cover


async def _set_number_of_contestants_in_race(
    raceclass: Dict,
    round: str,
    index: str,
    no_of_contestants: int,
    races: List[IndividualSprintRace],
) -> None:
    """Calculate and set number of contestants pr heat in round/index."""
    no_of_races = len(
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
            no_of_contestants,
            no_of_races,
        )
        if race.heat <= remainder:
            race.no_of_contestants = quotient + 1
        else:
            race.no_of_contestants = quotient

        # Check if no_of_contestants is greater than max:
        if race.no_of_contestants > race.max_no_of_contestants:
            raise IllegalValueInRaceError(
                f"Too many contestants in race with order {race.order}: {race.no_of_contestants}."
            )


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
        rule = {}
        try:
            rule = ConfigMatrix.m[_key]["from_to"][from_round][from_index]
        except KeyError:
            pass
        return rule

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
