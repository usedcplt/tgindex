"""CLI commands."""

import asyncio
import os
import sys

import structlog

from app.config import settings

logger = structlog.get_logger()


def run_server():
    """Run the API server."""
    import uvicorn

    port = int(os.getenv("PORT", settings.api.port))

    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=port,
        workers=settings.api.workers,
        reload=settings.debug,
    )


def run_worker():
    """Run the background worker."""
    from app.scheduler.jobs import SchedulerJobs

    scheduler = SchedulerJobs()
    scheduler.start()

    logger.info("worker_started")

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        scheduler.stop()
        logger.info("worker_stopped")


def run_migrate():
    """Run database migrations."""
    import subprocess

    subprocess.run(["alembic", "upgrade", "head"], check=True)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli.commands <command>")
        print("Commands: server, worker, migrate")
        sys.exit(1)

    command = sys.argv[1]

    if command == "server":
        run_server()
    elif command == "worker":
        run_worker()
    elif command == "migrate":
        run_migrate()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
