"""Drop db and recreate indexes."""
from typing import Any


async def drop_db_and_recreate_indexes(mongo: Any, db_name: str) -> None:
    """Drop db and recreate indexes."""
    await drop_db(mongo, db_name)

    db = mongo[f"{db_name}"]
    await create_indexes(db)


async def drop_db(mongo: Any, db_name: str) -> None:
    """Drop db."""
    await mongo.drop_database(f"{db_name}")


async def create_indexes(db: Any) -> None:
    """Create indexes."""
    # races_collection:
    await db.races_collection.create_index([("id", 1)], unique=True)
    await db.races_collection.create_index([("event_id", 1), ("order", 1)], unique=True)
    await db.races_collection.create_index(
        [("event_id", 1), ("raceclass", 1), ("order", 1)], unique=True
    )
    # race_results_collection:
    await db.race_results_collection.create_index([("id", 1)], unique=True)
    await db.race_results_collection.create_index(
        [("race_id", 1), ("timing_point", 1), ("id", 1)], unique=True
    )
    # start_entries_collection:
    await db.start_entries_collection.create_index([("id", 1)], unique=True)
    await db.start_entries_collection.create_index(
        [("race_id", 1), ("starting_position", 1)], unique=True
    )
    # time_events_collection:
    await db.time_events_collection.create_index([("id", 1)], unique=True)
    await db.time_events_collection.create_index(
        [("event_id", 1), ("id", 1)], unique=True
    )
    await db.time_events_collection.create_index(
        [("event_id", 1), ("timing_point", 1), ("id", 1)], unique=True
    )
    await db.time_events_collection.create_index(
        [("race_id", 1), ("id", 1)], unique=True
    )
