"""TGIndex main application entry point."""

import os
from pathlib import Path
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import Response, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.router import api_router
from app.dashboard.router import router as dashboard_router
from app.database.engine import engine
from app.scheduler.jobs import SchedulerJobs

logger = structlog.get_logger()

# Absolute paths for templates and static files
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "dashboard" / "static"

scheduler_jobs = SchedulerJobs()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("app_starting", version=settings.app_version)

    # Start scheduler for background crawling
    scheduler_jobs.start()
    logger.info("scheduler_started")

    yield

    # Shutdown
    scheduler_jobs.stop()
    await engine.dispose()
    logger.info("app_stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
app.include_router(api_router)
app.include_router(dashboard_router)


@app.api_route("/", methods=["GET", "HEAD"])
async def root(request: Request) -> Response:
    """Root endpoint with HEAD support for UptimeRobot."""
    if request.method == "HEAD":
        return Response(status_code=200)
    return PlainTextResponse(f"TGIndex v{settings.app_version} is running")


@app.get("/ping")
async def ping() -> dict:
    """Simple ping endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", settings.api.port))

    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=port,
        workers=settings.api.workers,
        reload=settings.debug,
    )
