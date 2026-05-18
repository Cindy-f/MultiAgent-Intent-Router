"""Unit tests for specialist tool execution (mocked Google workers)."""

from unittest.mock import MagicMock

import pytest

from src.agents import CalendarAgent, EmailAgent
from src.specialists.calendar_specialist import CalendarSpecialist
from src.specialists.email_specialist import EmailSpecialist
from src.google_tools import DailyScheduleResult


@pytest.fixture
def email_specialist():
    worker = MagicMock(spec=EmailAgent)
    worker.check_unread_emails.return_value = [
        {"from": "boss@co.com", "subject": "Standup"}
    ]
    return EmailSpecialist(MagicMock(), "test-mock", worker), worker


@pytest.fixture
def calendar_specialist():
    worker = MagicMock(spec=CalendarAgent)
    worker.fetch_daily_meeting_schedule.return_value = DailyScheduleResult(
        date="2026-05-16",
        time_zone="America/Chicago",
        events=[],
    )
    return CalendarSpecialist(MagicMock(), "test-mock", worker), worker


class TestEmailSpecialistTools:
    def test_check_unread_emails(self, email_specialist, metrics):
        spec, worker = email_specialist
        result = spec.execute_tool("check_unread_emails", {"maxResults": 5})
        worker.check_unread_emails.assert_called_once_with(5)
        assert result[0]["subject"] == "Standup"


class TestCalendarSpecialistTools:
    def test_fetch_daily_schedule(self, calendar_specialist, metrics, monkeypatch):
        spec, worker = calendar_specialist
        monkeypatch.setattr(
            "src.specialists.calendar_specialist.resolve_schedule_date",
            lambda d: "2026-05-16",
        )
        result = spec.execute_tool("fetch_daily_schedule", {"date": "2026-05-16"})
        worker.fetch_daily_meeting_schedule.assert_called_once_with("2026-05-16")
        assert result["date"] == "2026-05-16"
        assert result["events"] == []
