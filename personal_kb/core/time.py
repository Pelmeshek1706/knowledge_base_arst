from __future__ import annotations

from datetime import UTC, datetime

from personal_kb.core.errors import TimeError


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""

    return datetime.now(UTC)


def to_utc_datetime(value: datetime) -> datetime:
    """Normalize a datetime to UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 format."""

    return to_utc_iso(utc_now())


def to_utc_iso(value: datetime) -> str:
    """Convert a datetime to an ISO 8601 UTC string."""

    normalized = to_utc_datetime(value)
    return normalized.isoformat().replace("+00:00", "Z")


def parse_utc_datetime(value: str) -> datetime:
    """Parse an ISO 8601 timestamp and normalize it to UTC."""

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise TimeError(f"invalid ISO 8601 timestamp: {value!r}") from exc
    return to_utc_datetime(parsed)

