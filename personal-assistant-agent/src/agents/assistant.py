import os
from typing import Any, List

from src.agents.calendar_agent import CalendarAgent
from src.agents.email_agent import EmailAgent
from src.agents.time_agent import TimeAgent
from src.services.google_services_utils import GoogleServicesUtils
from src.tools.fetch_daily_meeting_schedule import DailyScheduleResult


class AssistantAgent:
    """Deprecated: use LlmCoordinator for chat, or specialist agents directly."""

    def __init__(self) -> None:
        self.google = GoogleServicesUtils(
            os.environ.get("CLIENT_ID", ""),
            os.environ.get("CLIENT_SECRET", ""),
            os.environ.get("REDIRECT_URI", ""),
        )
        self.email_agent = EmailAgent(self.google)
        self.calendar_agent = CalendarAgent(self.google)
        self.time_agent = TimeAgent()

    def authenticate(self) -> None:
        self.google.authenticate(
            [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/calendar.events.readonly",
            ]
        )

    def check_unread_emails(self, max_results: int = 10) -> List[dict[str, Any]]:
        return self.email_agent.check_unread_emails(max_results)

    def fetch_daily_meeting_schedule(self, date: str) -> DailyScheduleResult:
        return self.calendar_agent.fetch_daily_meeting_schedule(date)

    def get_current_time(self) -> str:
        return self.time_agent.get_current_time()
