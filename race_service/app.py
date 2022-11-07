"""Module for admin of races."""
import logging
import os
from typing import Any

from aiohttp import web
from aiohttp_middlewares import cors_middleware, error_middleware
import motor.motor_asyncio

from .views import (
    GenerateRaceplanForEventView,
    GenerateStartlistForEventView,
    Ping,
    RaceplansView,
    RaceplanView,
    RaceResultsView,
    RaceResultView,
    RacesView,
    RaceView,
    Ready,
    StartEntriesView,
    StartEntryView,
    StartlistsView,
    StartlistView,
    TimeEventsView,
    TimeEventView,
)


LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 27017))
DB_NAME = os.getenv("DB_NAME", "races")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


async def create_app() -> web.Application:
    """Create an web application."""
    app = web.Application(
        middlewares=[
            cors_middleware(allow_all=True),
            error_middleware(),  # default error handler for whole application
        ]
    )
    # Set up routes:
    app.add_routes(
        [
            web.view("/ping", Ping),
            web.view("/ready", Ready),
            web.view("/raceplans", RaceplansView),
            web.view(
                "/raceplans/generate-raceplan-for-event", GenerateRaceplanForEventView
            ),
            web.view("/raceplans/{raceplanId}", RaceplanView),
            web.view("/races", RacesView),
            web.view("/races/{raceId}", RaceView),
            web.view("/races/{raceId}/race-results", RaceResultsView),
            web.view("/races/{raceId}/race-results/{raceResultId}", RaceResultView),
            web.view("/races/{raceId}/start-entries", StartEntriesView),
            web.view("/races/{raceId}/start-entries/{startEntryId}", StartEntryView),
            web.view("/startlists", StartlistsView),
            web.view(
                "/startlists/generate-startlist-for-event",
                GenerateStartlistForEventView,
            ),
            web.view("/startlists/{startlistId}", StartlistView),
            web.view("/time-events", TimeEventsView),
            web.view("/time-events/{time_eventId}", TimeEventView),
        ]
    )

    # logging configurataion:
    logging.basicConfig(
        format="%(asctime)s,%(msecs)d %(levelname)s - %(module)s:%(lineno)d: %(message)s",
        datefmt="%H:%M:%S",
        level=LOGGING_LEVEL,
    )
    logging.getLogger("chardet.charsetprober").setLevel(LOGGING_LEVEL)

    async def mongo_context(app: Any) -> Any:
        # Set up database connection:
        logging.debug(f"Connecting to db at {DB_HOST}:{DB_PORT}")
        mongo = motor.motor_asyncio.AsyncIOMotorClient(
            host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASSWORD
        )
        db = mongo[f"{DB_NAME}"]
        app["db"] = db

        yield

        mongo.close()

    app.cleanup_ctx.append(mongo_context)

    return app
