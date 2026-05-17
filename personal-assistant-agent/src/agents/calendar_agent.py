from src.agents.base import BaseAgent
from src.tools.fetch_daily_meeting_schedule import (
    DailyScheduleResult,
    fetch_daily_meeting_schedule,
)


class CalendarAgent(BaseAgent):
    def fetch_daily_meeting_schedule(self, date: str) -> DailyScheduleResult:
        if not self.google.oauth2_client:
            raise RuntimeError("Google client not authenticated")
        return fetch_daily_meeting_schedule(self.google.oauth2_client, date)
