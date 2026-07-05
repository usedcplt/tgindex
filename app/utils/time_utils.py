"""Time utilities."""

from datetime import datetime, timedelta


def get_next_check_time(
    last_checked_at: datetime | None,
    member_count: int,
    health_score: float,
) -> datetime:
    """Calculate next check time based on chat activity."""
    now = datetime.utcnow()

    if last_checked_at is None:
        return now + timedelta(hours=1)

    # Base interval: 6 hours
    base_interval = timedelta(hours=6)

    # Adjust based on member count
    if member_count > 10000:
        base_interval = timedelta(hours=2)
    elif member_count > 1000:
        base_interval = timedelta(hours=4)
    elif member_count < 100:
        base_interval = timedelta(hours=12)

    # Adjust based on health score
    if health_score < 0.3:
        base_interval = timedelta(hours=24)
    elif health_score > 0.8:
        base_interval = base_interval * 0.5

    return last_checked_at + base_interval


def format_duration(seconds: float) -> str:
    """Format duration in human readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def is_recent(dt: datetime, minutes: int = 5) -> bool:
    """Check if datetime is recent."""
    if dt is None:
        return False
    return (datetime.utcnow() - dt).total_seconds() < minutes * 60
