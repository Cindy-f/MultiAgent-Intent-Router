import re
from datetime import date, datetime, time, timedelta, timezone

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def local_iso_date(when: date | None = None) -> str:
    """YYYY-MM-DD in the machine's local timezone (not UTC)."""
    return (when or date.today()).isoformat()


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
        return (date.today() + timedelta(days=1)).isoformat()

    # Models sometimes pass another tool's name (e.g. "get_current_time") — use today
    return local_iso_date()


def local_day_bounds(date_str: str) -> dict[str, str]:
    """RFC3339 bounds for one local calendar day (timeMax is start of next day)."""
    if not _ISO_DATE.match(date_str):
        raise ValueError(f"Invalid date: {date_str}. Use YYYY-MM-DD.")

    year, month, day = (int(date_str[0:4]), int(date_str[5:7]), int(date_str[8:10]))

    local_tz = datetime.now().astimezone().tzinfo
    start = datetime.combine(date(year, month, day), time.min, tzinfo=local_tz)
    end_exclusive = datetime.combine(
        date(year, month, day) + timedelta(days=1), time.min, tzinfo=local_tz
    )
    return {
        "timeMin": start.isoformat(),
        "timeMax": end_exclusive.isoformat(),
    }


def local_time_zone() -> str:
    return str(datetime.now().astimezone().tzinfo or timezone.utc)
