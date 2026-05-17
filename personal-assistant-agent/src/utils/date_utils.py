from datetime import date, datetime, time, timedelta, timezone


def local_iso_date(when: date | None = None) -> str:
    """YYYY-MM-DD in the machine's local timezone (not UTC)."""
    return (when or date.today()).isoformat()


def local_day_bounds(date_str: str) -> dict[str, str]:
    """RFC3339 bounds for one local calendar day (timeMax is start of next day)."""
    parts = date_str.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid date: {date_str}. Use YYYY-MM-DD.")
    year, month, day = (int(parts[0]), int(parts[1]), int(parts[2]))
    if not year or not month or not day:
        raise ValueError(f"Invalid date: {date_str}. Use YYYY-MM-DD.")

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
