from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return a timezone-naive UTC datetime for MySQL DATETIME storage."""

    return datetime.now(timezone.utc).replace(tzinfo=None)
