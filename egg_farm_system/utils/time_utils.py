"""Shared datetime helpers."""

from datetime import UTC, datetime


def utcnow_naive() -> datetime:
    """Return current UTC time as naive datetime for legacy DateTime columns."""
    return datetime.now(UTC).replace(tzinfo=None)
