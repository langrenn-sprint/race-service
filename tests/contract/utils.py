"""Utils for the contract tests."""


# ---
async def _decide_group_order_and_ranking(  # noqa: C901
    raceclass: dict,
) -> tuple[int, int, bool]:
    """Decide group, order, and ranking for a given raceclass."""
    if raceclass["name"] == "MS":
        return (1, 1, True)
    if raceclass["name"] == "KS":
        return (1, 2, True)
    if raceclass["name"] == "M19-20":
        return (1, 3, True)
    if raceclass["name"] == "K19-20":
        return (1, 4, True)
    if raceclass["name"] == "M18":
        return (2, 1, True)
    if raceclass["name"] == "K18":
        return (2, 2, True)
    if raceclass["name"] == "M17":
        return (3, 1, True)
    if raceclass["name"] == "K17":
        return (3, 2, True)
    if raceclass["name"] == "G16":
        return (4, 1, True)
    if raceclass["name"] == "J16":
        return (4, 2, True)
    if raceclass["name"] == "G15":
        return (4, 3, True)
    if raceclass["name"] == "J15":
        return (4, 4, True)
    if raceclass["name"] == "G14":
        return (5, 1, True)
    if raceclass["name"] == "J14":
        return (5, 2, True)
    if raceclass["name"] == "G13":
        return (5, 3, True)
    if raceclass["name"] == "J13":
        return (5, 4, True)
    if raceclass["name"] == "G12":
        return (6, 1, True)
    if raceclass["name"] == "J12":
        return (6, 2, True)
    if raceclass["name"] == "G11":
        return (6, 3, True)
    if raceclass["name"] == "J11":
        return (6, 4, True)
    if raceclass["name"] == "G10":
        return (7, 1, False)
    if raceclass["name"] == "J10":
        return (7, 2, False)
    if raceclass["name"] == "G9":
        return (8, 1, False)
    if raceclass["name"] == "J9":
        return (8, 2, False)
    return (0, 0, True)  # should not reach this point
