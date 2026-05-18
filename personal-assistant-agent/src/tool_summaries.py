"""Compact summaries for LLM context (smaller prompts, faster inference)."""

from __future__ import annotations

import os
from typing import Any, List

from src.google_tools import DailyScheduleResult

_SNIPPET_MAX = int(os.environ.get("EMAIL_SNIPPET_MAX_CHARS", "120"))


def _truncate(text: str, limit: int = _SNIPPET_MAX) -> str:
    text = (text or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def compact_email_list(emails: List[dict[str, Any]]) -> List[dict[str, str]]:
    compact: List[dict[str, str]] = []
    for item in emails:
        compact.append(
            {
                "from": str(item.get("from") or "Unknown"),
                "subject": str(item.get("subject") or "(no subject)"),
                "date": str(item.get("date") or ""),
                "snippet": _truncate(str(item.get("snippet") or "")),
            }
        )
    return compact


def format_emails_for_llm(emails: List[dict[str, Any]]) -> str:
    if not emails:
        return "No unread emails."
    lines: List[str] = []
    for i, item in enumerate(compact_email_list(emails), 1):
        lines.append(
            f"{i}. From: {item['from']} | Subject: {item['subject']} | {item['date']}"
        )
        if item["snippet"]:
            lines.append(f"   {item['snippet']}")
    return "\n".join(lines)


def format_schedule_for_llm(schedule: DailyScheduleResult) -> str:
    if not schedule.events:
        return f"No events on {schedule.date} ({schedule.time_zone})."
    lines = [f"Calendar for {schedule.date} ({schedule.time_zone}):"]
    for event in schedule.events:
        line = f"- {event.summary} ({event.time_window})"
        if event.link:
            line += f" [{event.link}]"
        lines.append(line)
    return "\n".join(lines)
