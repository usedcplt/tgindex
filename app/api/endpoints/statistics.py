"""Statistics API endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.repositories.source_repository import SourceRepository
from app.repositories.stats_repository import StatsRepository
from app.api.schemas.statistics import StatisticsResponse, SourceStats

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("", response_model=StatisticsResponse)
async def get_statistics(
    session: AsyncSession = Depends(get_session),
) -> StatisticsResponse:
    """Get current statistics."""
    stats_repo = StatsRepository(session)
    source_repo = SourceRepository(session)

    stats = await stats_repo.get_statistics()
    source_stats = await source_repo.get_source_stats()

    return StatisticsResponse(
        **stats,
        source_stats=[SourceStats(**s) for s in source_stats],
    )


@router.get("/sources", response_model=list[SourceStats])
async def get_source_statistics(
    session: AsyncSession = Depends(get_session),
) -> list[SourceStats]:
    """Get source statistics."""
    source_repo = SourceRepository(session)
    source_stats = await source_repo.get_source_stats()

    return [SourceStats(**s) for s in source_stats]


@router.get("/history")
async def get_statistics_history(
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Get historical statistics."""
    stats_repo = StatsRepository(session)
    return await stats_repo.get_historical_statistics(days)
