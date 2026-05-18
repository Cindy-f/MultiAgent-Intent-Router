"""Unit tests for supervisor delegation tools (no live LLM)."""

from unittest.mock import MagicMock

import pytest

from src.agents import TimeAgent
from src.supervisor import SupervisorAgent


@pytest.fixture
def supervisor():
    email = MagicMock()
    email.run.return_value = "Found manager: boss@example.com"
    calendar = MagicMock()
    calendar.run.return_value = "You have 3 meetings today."
    sup = SupervisorAgent(
        client=MagicMock(),
        model="test-mock",
        email_specialist=email,
        calendar_specialist=calendar,
        time_agent=TimeAgent(),
    )
    return sup, email, calendar


class TestSupervisorRunTool:
    def test_delegate_email(self, supervisor, metrics):
        sup, email, _ = supervisor
        result = sup._run_supervisor_tool(
            "delegate_to_email_agent",
            '{"task": "find manager email"}',
        )
        assert result["agent"] == "email"
        email.run.assert_called_once_with("find manager email", None)

    def test_delegate_calendar_with_prior_context(self, supervisor, metrics):
        sup, _, calendar = supervisor
        result = sup._run_supervisor_tool(
            "delegate_to_calendar_agent",
            '{"task": "afternoon free?", "prior_context": "boss@example.com"}',
        )
        assert result["agent"] == "calendar"
        calendar.run.assert_called_once_with("afternoon free?", "boss@example.com")

    def test_get_current_time(self, supervisor, metrics):
        sup, _, _ = supervisor
        result = sup._run_supervisor_tool("get_current_time", "{}")
        assert "display" in result
        assert "timezone" in result

    def test_empty_email_task_raises(self, supervisor, metrics):
        sup, _, _ = supervisor
        with pytest.raises(RuntimeError, match="non-empty task"):
            sup._run_supervisor_tool("delegate_to_email_agent", '{"task": ""}')

    def test_unknown_tool_raises(self, supervisor, metrics):
        sup, _, _ = supervisor
        with pytest.raises(RuntimeError, match="unknown tool"):
            sup._run_supervisor_tool("invalid_tool", "{}")
