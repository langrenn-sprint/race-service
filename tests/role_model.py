"""The role model for race-service, shared by the integration and contract tests.

See langrenn-sprint/event-service-gui#215. All GET operations are open. Every
write operation is listed here with the roles that may call it.
"""

ADMIN = "admin"
EVENT_ADMIN = "event-admin"
RESULT_ADMIN = "result-admin"
CONTESTANT_ADMIN = "contestant-admin"

ROLES = [ADMIN, EVENT_ADMIN, RESULT_ADMIN, CONTESTANT_ADMIN]
# Roles that no longer exist, and must not give access:
REMOVED_ROLES = ["user-admin", "race-result", "race-office"]

# Event setup, before raceday:
EVENT_SETUP = {ADMIN, EVENT_ADMIN}
# Results on raceday; event-admin keeps its raceday rights:
RESULTS = {ADMIN, EVENT_ADMIN, RESULT_ADMIN}
# Late entries on raceday: contestant-admin may add and change, not delete:
START_ENTRIES = {ADMIN, EVENT_ADMIN, RESULT_ADMIN, CONTESTANT_ADMIN}

WRITE_ACCESS: dict[tuple[str, str], set[str]] = {
    ("POST", "/raceplans/generate-raceplan-for-event"): EVENT_SETUP,
    ("POST", "/raceplans/{raceplan_id}/validate"): EVENT_SETUP,
    ("PUT", "/raceplans/{raceplan_id}"): EVENT_SETUP,
    ("DELETE", "/raceplans/{raceplan_id}"): EVENT_SETUP,
    ("PUT", "/races/{race_id}"): EVENT_SETUP,
    ("DELETE", "/races/{race_id}"): EVENT_SETUP,
    ("POST", "/startlists/generate-startlist-for-event"): EVENT_SETUP,
    ("DELETE", "/startlists/{startlist_id}"): EVENT_SETUP,
    ("PUT", "/races/{race_id}/race-results/{race_result_id}"): RESULTS,
    ("DELETE", "/races/{race_id}/race-results/{race_result_id}"): RESULTS,
    ("POST", "/time-events"): RESULTS,
    ("PUT", "/time-events/{time_event_id}"): RESULTS,
    ("DELETE", "/time-events/{time_event_id}"): RESULTS,
    ("POST", "/races/{race_id}/start-entries"): START_ENTRIES,
    ("PUT", "/races/{race_id}/start-entries/{start_entry_id}"): START_ENTRIES,
    ("DELETE", "/races/{race_id}/start-entries/{start_entry_id}"): RESULTS,
}


def access_cases(roles: list[str]) -> list[tuple[str, str, str, bool]]:
    """Return (method, path, role, allowed) for every write operation and role."""
    return [
        (method, path, role, role in allowed)
        for (method, path), allowed in WRITE_ACCESS.items()
        for role in roles
    ]
