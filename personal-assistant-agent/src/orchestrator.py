"""
Public entry point: Supervisor + specialists + Google OAuth (Main.ts equivalent).

Functional workers (agents.py) stay available for dashboard direct API access.
Google OAuth unchanged (google_auth.py / GoogleUtils).
"""

import os
from typing import List

from src.agents import CalendarAgent, EmailAgent, TimeAgent
from src.google_auth import GoogleServicesUtils
from src.llm_config import describe_llm_settings, resolve_llm_settings
from src.specialists.calendar_specialist import CalendarSpecialist
from src.specialists.email_specialist import EmailSpecialist
from src.supervisor import SupervisorAgent

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.events.readonly",
]


class LlmCoordinator:
    """
    Orchestrates the supervisor hierarchy.
    Backward-compatible name for app.py / dashboard.py.
    """

    def __init__(self) -> None:
        llm = resolve_llm_settings()
        self.openai = llm.client
        self.model = llm.model
        self.llm_label = f"Supervisor + specialists · {describe_llm_settings(llm)}"

        self.google = GoogleServicesUtils(
            os.environ.get("CLIENT_ID", ""),
            os.environ.get("CLIENT_SECRET", ""),
            os.environ.get("REDIRECT_URI", ""),
        )

        self.email_worker = EmailAgent(self.google)
        self.calendar_worker = CalendarAgent(self.google)
        self.time_agent = TimeAgent()

        self.email_specialist = EmailSpecialist(
            llm.client, llm.model, self.email_worker
        )
        self.calendar_specialist = CalendarSpecialist(
            llm.client, llm.model, self.calendar_worker
        )
        self.supervisor = SupervisorAgent(
            llm.client,
            llm.model,
            self.email_specialist,
            self.calendar_specialist,
            self.time_agent,
            self.email_worker,
            self.calendar_worker,
        )

    @property
    def email(self) -> EmailAgent:
        return self.email_worker

    @property
    def calendar(self) -> CalendarAgent:
        return self.calendar_worker

    @property
    def time(self) -> TimeAgent:
        return self.time_agent

    def authenticate(self) -> None:
        self.google.authenticate(GOOGLE_SCOPES)

    def reset_session(self) -> None:
        self.supervisor.reset_session()

    def chat(self, user_message: str) -> str:
        return self.supervisor.chat(user_message)
