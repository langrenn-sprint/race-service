"""Module for admin of races."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import motor.motor_asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters import (
    LivenessAdapter,
    RaceplansAdapter,
    RaceResultsAdapter,
    RacesAdapter,
    StartEntriesAdapter,
    StartlistsAdapter,
    TimeEventsAdapter,
)
from app.authorization import (
    TokenError,
    TokenMissingError,
    TokenValidationError,
)
from app.routers import (
    ping,
    race_results,
    raceplans,
    raceplans_commands,
    races,
    ready,
    start_entries,
    startlists,
    startlists_commands,
    time_events,
)
from app.utils import db_utils

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
DB_HOST = os.getenv("DB_HOST", "mongodb")
DB_PORT = int(os.getenv("DB_PORT", "27017"))
DB_NAME = os.getenv("DB_NAME", "races")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
CONFIG = os.getenv("CONFIG", "production")


class EndpointFilter(logging.Filter):
    """Logging filter to exclude specific endpoints from access logs."""

    def __init__(self, excluded_endpoints: list[str]) -> None:
        """Initialize the filter with a list of endpoints to exclude."""
        super().__init__()
        self.excluded_endpoints = excluded_endpoints

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover
        """Filter log records to exclude specified endpoints."""
        # Assuming the endpoint path is available in record.args[2]
        # for Uvicorn access logs
        if (  # noqa: SIM103
            record.args
            and len(record.args) >= 3  # noqa: PLR2004
            and record.args[2] in self.excluded_endpoints  # ty: ignore[invalid-argument-type]
        ):
            return False  # Exclude this log record
        return True  # Include this log record


logger = logging.getLogger("uvicorn.error")
access_logger = logging.getLogger("uvicorn.access")
# Exclude metrics and health check endpoint from access logs
excluded_endpoints = ["/health", "/metrics"]
access_logger.addFilter(EndpointFilter(excluded_endpoints))


@asynccontextmanager
async def lifespan(api: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001  # pragma: no cover
    """Initialize database and adapters on app startup."""
    # Initialize database:
    msg = f"Connecting to db at {DB_HOST}:{DB_PORT}"
    logger.debug(msg)
    mongo = motor.motor_asyncio.AsyncIOMotorClient(
        host=DB_HOST,
        port=DB_PORT,
        username=DB_USER,
        password=DB_PASSWORD,
        uuidRepresentation="standard",
    )
    db = mongo[f"{DB_NAME}"]

    await LivenessAdapter.init(db)
    await RaceplansAdapter.init(db)
    await RaceResultsAdapter.init(db)
    await RacesAdapter.init(db)
    await StartEntriesAdapter.init(db)
    await StartlistsAdapter.init(db)
    await TimeEventsAdapter.init(db)

    if CONFIG == "production":  # pragma: no cover
        # Create indexes:
        try:
            await db_utils.create_indexes(db)
        except Exception:
            logger.exception("Could not create indexes.")

    yield

    # Cleanup resources if needed
    mongo.close()


tags_metadata = [
    {
        "name": "raceplans",
        "description": "Operations on raceplans.",
    },
    {
        "name": "races",
        "description": "Operations on races.",
    },
    {
        "name": "race-results",
        "description": "Operations on race-results.",
    },
    {
        "name": "start-entries",
        "description": "Operations on start-entries.",
    },
    {
        "name": "startlists",
        "description": "Operations on startlists.",
    },
    {
        "name": "time-events",
        "description": "Operations on time-events.",
    },
    {
        "name": "liveness",
        "description": "Liveness and readiness endpoints.",
    },
]
api = FastAPI(
    lifespan=lifespan,
    title="Race Service",
    version="1.0.0",
    separate_input_output_schemas=False,
    openapi_tags=tags_metadata,
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.exception_handler(TokenError)
async def token_exception_handler(
    request: Request, exc: TokenError
) -> JSONResponse:  # pragma: no cover
    """Handle token validation errors."""
    _ = request  # Unused variable
    if isinstance(exc, TokenMissingError):
        return JSONResponse(
            status_code=401,
            content={"detail": "Not authenticated"},
        )
    if isinstance(exc, TokenValidationError):
        return JSONResponse(
            status_code=403,
            content={"detail": "Not authorized to access this resource"},
        )
    return JSONResponse(
        status_code=403,
        content={"detail": "Not authorized to access this resource"},
    )


# Set up routes:
api.include_router(ping.router)
api.include_router(ready.router)
api.include_router(raceplans_commands.router)
api.include_router(raceplans.router)
api.include_router(races.router)
api.include_router(race_results.router)
api.include_router(start_entries.router)
api.include_router(startlists_commands.router)
api.include_router(startlists.router)
api.include_router(time_events.router)
