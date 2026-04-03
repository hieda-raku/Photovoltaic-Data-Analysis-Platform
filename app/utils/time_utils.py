from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SYSTEM_TIMEZONE = "Asia/Shanghai"


def local_now_naive() -> datetime:
    """Return current system local time as naive datetime."""
    return datetime.now(ZoneInfo(SYSTEM_TIMEZONE)).replace(tzinfo=None)


def utc_millis_to_local_naive(timestamp_millis: float) -> datetime:
    """Convert UTC timestamp in milliseconds to system local naive datetime."""
    utc_dt = datetime.fromtimestamp(timestamp_millis / 1000, tz=timezone.utc)
    local_dt = utc_dt.astimezone(ZoneInfo(SYSTEM_TIMEZONE))
    return local_dt.replace(tzinfo=None)
