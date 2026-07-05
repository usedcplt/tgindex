"""TGIndex main application entry point."""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.router import api_router
from app.dashboard.router import router as dashboard_router
from app.database.engine import engine
from app.scheduler.jobs import SchedulerJobs

logger = structlog.get_logger()

scheduler_jobs = SchedulerJobs()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("app_starting", version=settings.app_version)

    # Start scheduler
    scheduler_jobs.start()

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

# Mount static files
app.mount("/static", StaticFiles(directory="app/dashboard/static"), name="static")

# Include routers
app.include_router(api_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "dashboard": "/dashboard",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=settings.api.port,
        workers=settings.api.workers,
        reload=settings.debug,
    )
