import os
from typing import Any, Dict, List

from src.google_auth import GoogleServicesUtils
from src.google_cache import TimedCache
from src.google_tools import (
    DEFAULT_UNREAD_MAX,
    DailyScheduleResult,
    fetch_daily_meeting_schedule,
    get_current_time,
    get_unread_emails,
)


class BaseAgent:
    def __init__(self, google: GoogleServicesUtils) -> None:
        self.google = google


class EmailAgent(BaseAgent):
    def __init__(self, google: GoogleServicesUtils) -> None:
        super().__init__(google)
        self._unread_cache: TimedCache[List[dict[str, Any]]] = TimedCache()

    def check_unread_emails(
        self, max_results: int = DEFAULT_UNREAD_MAX, *, use_cache: bool = True
    ) -> List[dict[str, Any]]:
        if not self.google.oauth2_client:
            raise RuntimeError("Google client not authenticated")

        limit = max(1, min(int(max_results), 20))
        if use_cache:
            cached = self._unread_cache.get()
            if cached is not None:
                return cached[:limit]

        emails = get_unread_emails(self.google.oauth2_client, limit)
        self._unread_cache.set(emails)
        return emails

    def clear_cache(self) -> None:
        self._unread_cache.clear()


class CalendarAgent(BaseAgent):
    def __init__(self, google: GoogleServicesUtils) -> None:
        super().__init__(google)
        self._schedule_cache: TimedCache[DailyScheduleResult] = TimedCache()

    def fetch_daily_meeting_schedule(
        self, date: str, *, use_cache: bool = True
    ) -> DailyScheduleResult:
        if not self.google.oauth2_client:
            raise RuntimeError("Google client not authenticated")

        if use_cache:
            cached = self._schedule_cache.get()
            if cached is not None and cached.date == date:
                return cached

        schedule = fetch_daily_meeting_schedule(self.google.oauth2_client, date)
        self._schedule_cache.set(schedule)
        return schedule

    def clear_cache(self) -> None:
        self._schedule_cache.clear()


class TimeAgent:
    def get_current_time(self) -> Dict[str, Any]:
        return get_current_time()
