"""
UTC Timezone utilities for RailFleet Manager.

All backend operations MUST use UTC. This module provides helper functions
to ensure UTC compliance across the application.
"""
from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Returns:
        datetime: Current UTC time with tzinfo=timezone.utc

    Example:
        >>> from src.core.timezone import utc_now
        >>> now = utc_now()
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """
    Get current UTC time as naive datetime (for SQLAlchemy compatibility).

    Returns:
        datetime: Current UTC time without timezone info

    Note:
        Use this for SQLAlchemy default= parameters:
        >>> created_at = Column(DateTime, default=utc_now_naive)
    """
    return datetime.utcnow()


def to_utc(dt: datetime) -> datetime:
    """
    Convert any datetime to UTC.

    Args:
        dt: Datetime to convert (naive or aware)

    Returns:
        datetime: Timezone-aware datetime in UTC

    Example:
        >>> from datetime import datetime
        >>> naive_dt = datetime(2025, 11, 23, 10, 30)
        >>> utc_dt = to_utc(naive_dt)
        >>> utc_dt.tzinfo
        datetime.timezone.utc
    """
    if dt.tzinfo is None:
        # Assume naive datetime is already UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Convert aware datetime to UTC
        return dt.astimezone(timezone.utc)


def format_iso8601(dt: datetime) -> str:
    """
    Format datetime as ISO 8601 with explicit 'Z' suffix (UTC indicator).

    Args:
        dt: Datetime to format (will be converted to UTC if not already)

    Returns:
        str: ISO 8601 formatted string with 'Z' suffix

    Example:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2025, 11, 23, 10, 30, 0, tzinfo=timezone.utc)
        >>> format_iso8601(dt)
        '2025-11-23T10:30:00Z'
    """
    utc_dt = to_utc(dt)
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_iso8601(dt_str: str) -> datetime:
    """
    Parse ISO 8601 datetime string to UTC datetime.

    Args:
        dt_str: ISO 8601 formatted string (with or without 'Z')

    Returns:
        datetime: Timezone-aware datetime in UTC

    Example:
        >>> dt = parse_iso8601("2025-11-23T10:30:00Z")
        >>> dt.tzinfo
        datetime.timezone.utc
    """
    # Handle 'Z' suffix
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + '+00:00'

    dt = datetime.fromisoformat(dt_str)
    return to_utc(dt)


def validate_utc_aware(dt: Optional[datetime]) -> bool:
    """
    Validate that a datetime is UTC-aware.

    Args:
        dt: Datetime to validate

    Returns:
        bool: True if datetime is UTC-aware, False otherwise

    Example:
        >>> from datetime import datetime, timezone
        >>> dt_utc = datetime.now(timezone.utc)
        >>> validate_utc_aware(dt_utc)
        True
        >>> dt_naive = datetime.now()
        >>> validate_utc_aware(dt_naive)
        False
    """
    if dt is None:
        return True  # None is valid (optional field)

    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


# Constants
UTC = timezone.utc


# Deprecation warnings for common mistakes
def _deprecated_now():
    """DO NOT USE: Use utc_now() or utc_now_naive() instead."""
    raise DeprecationWarning(
        "Do not use datetime.now() in backend code! "
        "Use utc_now() or utc_now_naive() from src.core.timezone instead."
    )


# Export main functions
__all__ = [
    'utc_now',
    'utc_now_naive',
    'to_utc',
    'format_iso8601',
    'parse_iso8601',
    'validate_utc_aware',
    'UTC',
]
