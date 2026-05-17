from typing import Any, Dict, List

from src.google_auth import GoogleServicesUtils
from src.google_tools import (
    DailyScheduleResult,
    fetch_daily_meeting_schedule,
    get_current_time,
    get_unread_emails,
)


class BaseAgent:
    def __init__(self, google: GoogleServicesUtils) -> None:
        self.google = google


class EmailAgent(BaseAgent):
    def check_unread_emails(self, max_results: int = 10) -> List[dict[str, Any]]:
        if not self.google.oauth2_client:
            raise RuntimeError("Google client not authenticated")
        return get_unread_emails(self.google.oauth2_client, max_results)


class CalendarAgent(BaseAgent):
    def fetch_daily_meeting_schedule(self, date: str) -> DailyScheduleResult:
        if not self.google.oauth2_client:
            raise RuntimeError("Google client not authenticated")
        return fetch_daily_meeting_schedule(self.google.oauth2_client, date)


class TimeAgent:
    def get_current_time(self) -> Dict[str, Any]:
        return get_current_time()
