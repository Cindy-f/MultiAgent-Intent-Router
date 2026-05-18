"""Fast paths: minimal LLM hops for common intents."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Optional

from src.dates import local_iso_date
from src.intent_router import Intent, classify_intent
from src.telemetry import chat_completion, telemetry
from src.tool_summaries import format_emails_for_llm, format_schedule_for_llm

if TYPE_CHECKING:
    from src.agents import CalendarAgent, EmailAgent, TimeAgent
    from openai import OpenAI

_SYNTHESIS_SYSTEM = """You are a concise personal assistant.
Answer the user using ONLY the data provided below. Do not invent emails or events.
Be brief and friendly."""


def try_fast_reply(
    *,
    client: "OpenAI",
    model: str,
    message: str,
    email_worker: "EmailAgent",
    calendar_worker: "CalendarAgent",
    time_agent: "TimeAgent",
) -> Optional[str]:
    intent = classify_intent(message)

    if intent == Intent.TIME:
        return _reply_time(time_agent)

    if intent == Intent.UNREAD_EMAIL:
        return _reply_unread(client, model, message, email_worker)

    if intent == Intent.CALENDAR_TODAY:
        return _reply_calendar_today(client, model, message, calendar_worker)

    if intent == Intent.BRIEFING:
        return _reply_briefing(client, model, message, email_worker, calendar_worker)

    if intent == Intent.EMAIL_AND_CALENDAR:
        return _reply_email_and_calendar(
            client, model, message, email_worker, calendar_worker
        )

    return None


def _reply_time(time_agent: "TimeAgent") -> str:
    with telemetry.tool("fast", "get_current_time"):
        info = time_agent.get_current_time()
    display = info.get("display") or info.get("iso") or "unknown"
    return f"It's currently {display}."


def _one_shot_synthesis(client: "OpenAI", model: str, user_prompt: str) -> str:
    response = chat_completion(
        client,
        agent="fast",
        label="synthesis",
        model=model,
        messages=[
            {"role": "system", "content": _SYNTHESIS_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )
    message = response.choices[0].message
    return (message.content or "").strip() or "(No response)"


def _reply_unread(
    client: "OpenAI", model: str, message: str, email_worker: "EmailAgent"
) -> str:
    with telemetry.tool("fast", "check_unread_emails"):
        emails = email_worker.check_unread_emails()
    data = format_emails_for_llm(emails)
    prompt = f"User question: {message}\n\nUnread inbox:\n{data}"
    return _one_shot_synthesis(client, model, prompt)


def _reply_calendar_today(
    client: "OpenAI", model: str, message: str, calendar_worker: "CalendarAgent"
) -> str:
    today = local_iso_date()
    with telemetry.tool("fast", "fetch_daily_schedule"):
        schedule = calendar_worker.fetch_daily_meeting_schedule(today)
    data = format_schedule_for_llm(schedule)
    prompt = f"User question: {message}\n\n{data}"
    return _one_shot_synthesis(client, model, prompt)


def _fetch_briefing_data(
    email_worker: "EmailAgent", calendar_worker: "CalendarAgent"
) -> tuple[str, str]:
    today = local_iso_date()

    def _emails() -> str:
        with telemetry.tool("fast", "check_unread_emails"):
            return format_emails_for_llm(email_worker.check_unread_emails())

    def _calendar() -> str:
        with telemetry.tool("fast", "fetch_daily_schedule"):
            schedule = calendar_worker.fetch_daily_meeting_schedule(today)
            return format_schedule_for_llm(schedule)

    with ThreadPoolExecutor(max_workers=2) as pool:
        email_future = pool.submit(_emails)
        cal_future = pool.submit(_calendar)
        return email_future.result(), cal_future.result()


def _reply_briefing(
    client: "OpenAI",
    model: str,
    message: str,
    email_worker: "EmailAgent",
    calendar_worker: "CalendarAgent",
) -> str:
    inbox, calendar = _fetch_briefing_data(email_worker, calendar_worker)
    prompt = (
        f"User question: {message}\n\n"
        f"## Unread email\n{inbox}\n\n## Calendar today\n{calendar}\n\n"
        "Give a short morning briefing covering both."
    )
    return _one_shot_synthesis(client, model, prompt)


def _reply_email_and_calendar(
    client: "OpenAI",
    model: str,
    message: str,
    email_worker: "EmailAgent",
    calendar_worker: "CalendarAgent",
) -> str:
    inbox, calendar = _fetch_briefing_data(email_worker, calendar_worker)
    prompt = (
        f"User question: {message}\n\n"
        f"## Unread email (scan for people/topics mentioned)\n{inbox}\n\n"
        f"## Calendar today\n{calendar}\n\n"
        "Answer the full question using only this data."
    )
    return _one_shot_synthesis(client, model, prompt)
