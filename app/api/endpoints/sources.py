"""Sources API endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.repositories.source_repository import SourceRepository

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
async def list_sources(
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """List all discovery sources."""
    source_repo = SourceRepository(session)
    sources = await source_repo.get_all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "url": s.url,
            "is_enabled": s.is_enabled,
            "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
            "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
            "total_found": s.total_found,
            "total_errors": s.total_errors,
        }
        for s in sources
    ]


@router.post("/{source_id}/run")
async def run_source(
    source_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Trigger a source run."""
    source_repo = SourceRepository(session)
    source = await source_repo.get_by_id(source_id)

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # TODO: Trigger actual source run
    return {
        "status": "triggered",
        "source_id": source_id,
        "source_name": source.name,
    }
