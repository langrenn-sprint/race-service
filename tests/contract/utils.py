"""Utils for the contract tests."""


# ---
async def _decide_group_order_and_ranking(  # noqa: C901
    raceclass: dict,
) -> tuple[int, int, bool]:
    """Decide group, order, and ranking for a given raceclass."""
    if raceclass["name"] == "Menn senior".replace(" ", ""):
        return (1, 1, True)
    if raceclass["name"] == "Kvinner senior".replace(" ", ""):
        return (1, 2, True)
    if raceclass["name"] == "Menn 19-20".replace(" ", ""):
        return (1, 3, True)
    if raceclass["name"] == "Kvinner 19-20".replace(" ", ""):
        return (1, 4, True)
    if raceclass["name"] == "Menn 18".replace(" ", ""):
        return (2, 1, True)
    if raceclass["name"] == "Kvinner 18".replace(" ", ""):
        return (2, 2, True)
    if raceclass["name"] == "Menn 17".replace(" ", ""):
        return (3, 1, True)
    if raceclass["name"] == "Kvinner 17".replace(" ", ""):
        return (3, 2, True)
    if raceclass["name"] == "G 16 år".replace(" ", ""):
        return (4, 1, True)
    if raceclass["name"] == "J 16 år".replace(" ", ""):
        return (4, 2, True)
    if raceclass["name"] == "G 15 år".replace(" ", ""):
        return (4, 3, True)
    if raceclass["name"] == "J 15 år".replace(" ", ""):
        return (4, 4, True)
    if raceclass["name"] == "G 14 år".replace(" ", ""):
        return (5, 1, True)
    if raceclass["name"] == "J 14 år".replace(" ", ""):
        return (5, 2, True)
    if raceclass["name"] == "G 13 år".replace(" ", ""):
        return (5, 3, True)
    if raceclass["name"] == "J 13 år".replace(" ", ""):
        return (5, 4, True)
    if raceclass["name"] == "G 12 år".replace(" ", ""):
        return (6, 1, True)
    if raceclass["name"] == "J 12 år".replace(" ", ""):
        return (6, 2, True)
    if raceclass["name"] == "G 11 år".replace(" ", ""):
        return (6, 3, True)
    if raceclass["name"] == "J 11 år".replace(" ", ""):
        return (6, 4, True)
    if raceclass["name"] == "G 10 år".replace(" ", ""):
        return (7, 1, False)
    if raceclass["name"] == "J 10 år".replace(" ", ""):
        return (7, 2, False)
    if raceclass["name"] == "G 9 år".replace(" ", ""):
        return (8, 1, False)
    if raceclass["name"] == "J 9 år".replace(" ", ""):
        return (8, 2, False)
    return (0, 0, True)  # should not reach this point
