"""Module for admin of races."""
import logging
import os
from typing import Any

from aiohttp import web
from aiohttp_middlewares import cors_middleware, error_middleware
import motor.motor_asyncio

from .views import (
    GenerateRaceplanForEventView,
    Ping,
    RaceplansView,
    RaceplanView,
    Ready,
)


LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 27017))
DB_NAME = os.getenv("DB_NAME", "test")
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
    # Set up logging
    logging.basicConfig(level=LOGGING_LEVEL)
    logging.getLogger("chardet.charsetprober").setLevel(LOGGING_LEVEL)

    # Set up database connection:
    logging.debug(f"Connecting to db at {DB_HOST}:{DB_PORT}")
    mongo = motor.motor_asyncio.AsyncIOMotorClient(DB_HOST, DB_PORT)
    db = mongo.DB_NAME
    app["db"] = db

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
        ]
    )

    async def cleanup(app: Any) -> None:
        mongo.close()

    app.on_cleanup.append(cleanup)

    return app