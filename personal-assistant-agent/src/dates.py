import os
import re
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from typing import Any
from zoneinfo import ZoneInfo

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def get_local_tzinfo() -> tzinfo:
    """System timezone, or LOCAL_TIMEZONE from .env (e.g. America/Chicago for Austin, TX)."""
    name = (os.environ.get("LOCAL_TIMEZONE") or "").strip()
    if name:
        return ZoneInfo(name)
    return datetime.now().astimezone().tzinfo or timezone.utc


def local_now() -> datetime:
    return datetime.now(get_local_tzinfo())


def local_iso_date(when: date | None = None) -> str:
    """YYYY-MM-DD in local timezone (not UTC)."""
    return (when or local_now().date()).isoformat()


def local_now_info() -> dict[str, Any]:
    """Current local time for the user-facing clock tool."""
    now = local_now()
    time_12 = now.strftime("%I:%M %p").lstrip("0") or now.strftime("%I:%M %p")
    return {
        "iso": now.isoformat(),
        "timezone": local_time_zone(),
        "localDate": now.date().isoformat(),
        "localTime": time_12,
        "display": f"{time_12} on {now.strftime('%A, %B %d, %Y')}",
    }


def resolve_schedule_date(date_arg: object | None) -> str:
    """Normalize LLM date args; invalid values default to local today."""
    if date_arg is None:
        return local_iso_date()
    if not isinstance(date_arg, str):
        return local_iso_date()

    raw = date_arg.strip()
    if not raw:
        return local_iso_date()

    if _ISO_DATE.match(raw):
        return raw

    lowered = raw.lower()
    if lowered in ("today", "now"):
        return local_iso_date()
    if lowered == "tomorrow":
        return (local_now().date() + timedelta(days=1)).isoformat()

    # Models sometimes pass another tool's name (e.g. "get_current_time") — use today
    return local_iso_date()


def local_day_bounds(date_str: str) -> dict[str, str]:
    """RFC3339 bounds for one local calendar day (timeMax is start of next day)."""
    if not _ISO_DATE.match(date_str):
        raise ValueError(f"Invalid date: {date_str}. Use YYYY-MM-DD.")

    year, month, day = (int(date_str[0:4]), int(date_str[5:7]), int(date_str[8:10]))

    local_tz = get_local_tzinfo()
    start = datetime.combine(date(year, month, day), time.min, tzinfo=local_tz)
    end_exclusive = datetime.combine(
        date(year, month, day) + timedelta(days=1), time.min, tzinfo=local_tz
    )
    return {
        "timeMin": start.isoformat(),
        "timeMax": end_exclusive.isoformat(),
    }


def local_time_zone() -> str:
    name = (os.environ.get("LOCAL_TIMEZONE") or "").strip()
    if name:
        return name
    tz = get_local_tzinfo()
    if hasattr(tz, "key"):
        return str(tz.key)
    return str(tz)
