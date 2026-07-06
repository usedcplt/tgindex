"""APScheduler job definitions."""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

import structlog

from app.config import settings
from app.database.engine import session_factory
from app.crawler.search_engine import SearchEngineSource
from app.crawler.catalog_source import CatalogSource
from app.crawler.github_source import GitHubSource
from app.crawler.reddit_source import RedditSource
from app.crawler.recursive_source import RecursiveSource
from app.crawler.telegram_search_source import TelegramSearchSource
from app.workers.discovery_worker import DiscoveryWorker
from app.workers.metadata_worker import MetadataWorker
from app.workers.update_worker import UpdateWorker
from app.workers.validation_worker import ValidationWorker

logger = structlog.get_logger()


def log_activity(job: str, status: str, details: dict | None = None) -> None:
    """Log activity to the activity tracker."""
    try:
        from app.api.endpoints.system import add_activity
        add_activity(job, status, details)
    except ImportError:
        pass


class SchedulerJobs:
    """Manages scheduled jobs."""

    def __init__(self) -> None:
        jobstores = {"default": MemoryJobStore()}
        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 300,
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            job_defaults=job_defaults,
        )

    def setup_jobs(self) -> None:
        """Setup all scheduled jobs."""
        # Discovery every 10 seconds
        self.scheduler.add_job(
            self._run_discovery,
            "interval",
            seconds=10,
            id="discovery_job",
            name="Discovery",
        )

        # Validation every 10 seconds
        self.scheduler.add_job(
            self._run_validation,
            "interval",
            seconds=10,
            id="validation_job",
            name="Validation",
        )

        # Metadata extraction every 10 seconds
        self.scheduler.add_job(
            self._run_metadata_extraction,
            "interval",
            seconds=10,
            id="metadata_job",
            name="Metadata",
        )

        # Retry errors every 5 minutes
        self.scheduler.add_job(
            self._run_retry_errors,
            "interval",
            minutes=5,
            id="retry_job",
            name="RetryErrors",
        )

        # Cleanup stuck processing every minute
        self.scheduler.add_job(
            self._run_cleanup_stuck,
            "interval",
            minutes=1,
            id="cleanup_job",
            name="CleanupStuck",
        )

        # Update every 2 hours
        self.scheduler.add_job(
            self._run_update,
            "interval",
            hours=2,
            id="update_job",
            name="Update",
        )

        logger.info("scheduler_jobs_setup")
        log_activity("scheduler", "started", {"jobs": ["discovery", "validation", "metadata", "retry", "cleanup", "update"]})

    def start(self) -> None:
        """Start the scheduler."""
        self.setup_jobs()
        self.scheduler.start()
        logger.info("scheduler_started")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("scheduler_stopped")

    async def _run_discovery(self) -> None:
        """Run discovery job."""
        log_activity("discovery", "running")
        try:
            async with session_factory() as session:
                sources = [
                    TelegramSearchSource("telegram_search"),
                    SearchEngineSource("search_engine"),
                    CatalogSource("catalog"),
                    GitHubSource("github"),
                    RedditSource("reddit"),
                    RecursiveSource(session, "recursive"),
                ]
                worker = DiscoveryWorker(session, sources)
                result = await worker.run()
                log_activity("discovery", "completed", result)
                logger.info("discovery_completed", result=result)
        except Exception as e:
            log_activity("discovery", "failed", {"error": str(e)})
            logger.error("discovery_failed", error=str(e))

    async def _run_validation(self) -> None:
        """Run validation job."""
        log_activity("validation", "running")
        try:
            async with session_factory() as session:
                worker = ValidationWorker(session)
                result = await worker.run()
                log_activity("validation", "completed", result)
                logger.info("validation_completed", result=result)
        except Exception as e:
            log_activity("validation", "failed", {"error": str(e)})
            logger.error("validation_failed", error=str(e))

    async def _run_metadata_extraction(self) -> None:
        """Run metadata extraction job."""
        log_activity("metadata", "running")
        try:
            async with session_factory() as session:
                worker = MetadataWorker(session)
                result = await worker.run()
                log_activity("metadata", "completed", result)
                logger.info("metadata_completed", result=result)
        except Exception as e:
            log_activity("metadata", "failed", {"error": str(e)})
            logger.error("metadata_failed", error=str(e))

    async def _run_retry_errors(self) -> None:
        """Retry error URLs."""
        try:
            from app.repositories.queue_repository import QueueRepository
            async with session_factory() as session:
                queue_repo = QueueRepository(session)
                retried = await queue_repo.retry_errors(max_retries=3)
                if retried > 0:
                    logger.info("retry_errors", retried=retried)
        except Exception as e:
            logger.error("retry_failed", error=str(e))

    async def _run_cleanup_stuck(self) -> None:
        """Clean up stuck processing URLs."""
        try:
            from app.repositories.queue_repository import QueueRepository
            async with session_factory() as session:
                queue_repo = QueueRepository(session)
                reset = await queue_repo.reset_stuck_processing(timeout_minutes=10)
                if reset > 0:
                    logger.info("cleanup_stuck", reset=reset)
        except Exception as e:
            logger.error("cleanup_failed", error=str(e))

    async def _run_update(self) -> None:
        """Run update job."""
        log_activity("update", "running")
        try:
            async with session_factory() as session:
                worker = UpdateWorker(session)
                result = await worker.run()
                log_activity("update", "completed", result)
                logger.info("update_completed", result=result)
        except Exception as e:
            log_activity("update", "failed", {"error": str(e)})
            logger.error("update_failed", error=str(e))
