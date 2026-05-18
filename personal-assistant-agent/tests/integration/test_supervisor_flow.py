"""Integration tests: supervisor + specialists with mocked OpenAI."""

from unittest.mock import MagicMock

import pytest

from src.agents import TimeAgent
from src.specialists.calendar_specialist import CalendarSpecialist
from src.specialists.email_specialist import EmailSpecialist
from src.supervisor import SupervisorAgent
from tests.helpers.mock_openai import (
    MockLLMResponse,
    MockOpenAIClient,
    MockUsage,
    make_tool_call,
)


def _build_supervisor(mock_client: MockOpenAIClient) -> tuple[SupervisorAgent, MockOpenAIClient]:
    client = mock_client.as_openai_client()

    email_worker = MagicMock()
    email_worker.check_unread_emails.return_value = [
        {"from": "Manager <mgr@co.com>", "subject": "Sync"}
    ]

    calendar_worker = MagicMock()
    calendar_worker.fetch_daily_meeting_schedule.return_value = MagicMock(
        to_dict=lambda: {
            "date": "2026-05-16",
            "timeZone": "America/Chicago",
            "events": [{"summary": "Standup", "timeWindow": "9:00 AM – 10:00 AM"}],
        }
    )

    email_spec = EmailSpecialist(client, "gpt-4o-mini", email_worker)
    calendar_spec = CalendarSpecialist(client, "gpt-4o-mini", calendar_worker)

    supervisor = SupervisorAgent(
        client,
        "gpt-4o-mini",
        email_spec,
        calendar_spec,
        TimeAgent(),
    )
    return supervisor, mock_client


class TestSupervisorCalendarFlow:
    def test_calendar_question_end_to_end(self, metrics):
        mock = MockOpenAIClient(
            responses=[
                MockLLMResponse(
                    tool_calls=[
                        make_tool_call(
                            "delegate_to_calendar_agent",
                            '{"task": "What is on the calendar today?"}',
                            "call_sup_1",
                        )
                    ],
                    usage=MockUsage(80, 20),
                ),
                MockLLMResponse(
                    content="You have a Standup at 9:00 AM.",
                    usage=MockUsage(120, 40),
                ),
                MockLLMResponse(
                    content="Today you have Standup at 9:00 AM.",
                    usage=MockUsage(60, 30),
                ),
            ],
            simulated_latency_ms=2.0,
        )
        supervisor, mock = _build_supervisor(mock)
        metrics["model"] = "gpt-4o-mini"
        metrics["prompt_tokens"] = 0
        metrics["completion_tokens"] = 0

        reply = supervisor.chat("What is on my calendar today?")

        assert "Standup" in reply or "9" in reply
        metrics["prompt_tokens"] = mock.total_prompt_tokens
        metrics["completion_tokens"] = mock.total_completion_tokens
        assert mock.call_count >= 2


class TestSupervisorEmailFlow:
    def test_email_question_end_to_end(self, metrics):
        mock = MockOpenAIClient(
            responses=[
                MockLLMResponse(
                    tool_calls=[
                        make_tool_call(
                            "delegate_to_email_agent",
                            '{"task": "List unread emails"}',
                            "call_sup_1",
                        )
                    ],
                    usage=MockUsage(70, 15),
                ),
                MockLLMResponse(
                    tool_calls=[
                        make_tool_call("check_unread_emails", '{"maxResults": 10}', "call_em_1")
                    ],
                    usage=MockUsage(90, 25),
                ),
                MockLLMResponse(
                    content="Unread: Sync from Manager.",
                    usage=MockUsage(100, 35),
                ),
                MockLLMResponse(
                    content="You have one unread email from Manager about Sync.",
                    usage=MockUsage(80, 30),
                ),
            ],
            simulated_latency_ms=2.0,
        )
        supervisor, mock = _build_supervisor(mock)
        metrics["model"] = "gpt-4o-mini"

        reply = supervisor.chat("What unread emails do I have?")

        assert "Manager" in reply or "Sync" in reply or "unread" in reply.lower()
        metrics["prompt_tokens"] = mock.total_prompt_tokens
        metrics["completion_tokens"] = mock.total_completion_tokens


class TestSupervisorMultiStepFlow:
    def test_email_then_calendar_handoff(self, metrics):
        mock = MockOpenAIClient(
            responses=[
                MockLLMResponse(
                    tool_calls=[
                        make_tool_call(
                            "delegate_to_email_agent",
                            '{"task": "Find manager email"}',
                            "call_1",
                        )
                    ],
                    usage=MockUsage(60, 20),
                ),
                MockLLMResponse(
                    tool_calls=[
                        make_tool_call("check_unread_emails", "{}", "call_2")
                    ],
                    usage=MockUsage(70, 25),
                ),
                MockLLMResponse(
                    content="Manager email is mgr@co.com",
                    usage=MockUsage(80, 30),
                ),
                MockLLMResponse(
                    tool_calls=[
                        make_tool_call(
                            "delegate_to_calendar_agent",
                            '{"task": "Afternoon availability?", "prior_context": "mgr@co.com"}',
                            "call_3",
                        )
                    ],
                    usage=MockUsage(90, 25),
                ),
                MockLLMResponse(
                    tool_calls=[
                        make_tool_call("fetch_daily_schedule", "{}", "call_4")
                    ],
                    usage=MockUsage(85, 30),
                ),
                MockLLMResponse(
                    content="Afternoon is free except Standup.",
                    usage=MockUsage(75, 28),
                ),
                MockLLMResponse(
                    content="Manager is mgr@co.com; you have Standup at 9 AM.",
                    usage=MockUsage(100, 40),
                ),
            ],
            simulated_latency_ms=1.0,
        )
        supervisor, mock = _build_supervisor(mock)
        metrics["model"] = "gpt-4o-mini"

        reply = supervisor.chat(
            "Find my manager's email and tell me if I'm free this afternoon."
        )

        assert len(reply) > 10
        metrics["prompt_tokens"] = mock.total_prompt_tokens
        metrics["completion_tokens"] = mock.total_completion_tokens
        assert mock.call_count >= 4


class TestSupervisorTimeTool:
    def test_time_question(self, metrics):
        mock = MockOpenAIClient(
            responses=[
                MockLLMResponse(
                    tool_calls=[
                        make_tool_call("get_current_time", "{}", "call_time")
                    ],
                    usage=MockUsage(40, 10),
                ),
                MockLLMResponse(
                    content="The current time is 8:57 PM on Saturday, May 16, 2026.",
                    usage=MockUsage(50, 20),
                ),
            ],
            simulated_latency_ms=1.0,
        )
        supervisor, mock = _build_supervisor(mock)
        metrics["model"] = "gpt-4o-mini"

        reply = supervisor.chat("What time is it now?")

        assert "PM" in reply or "AM" in reply or "time" in reply.lower()
        metrics["prompt_tokens"] = mock.total_prompt_tokens
        metrics["completion_tokens"] = mock.total_completion_tokens
