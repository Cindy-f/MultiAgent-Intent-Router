"""Lightweight intent classification for fast paths (no LLM)."""

from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    TIME = "time"
    UNREAD_EMAIL = "unread_email"
    CALENDAR_TODAY = "calendar_today"
    BRIEFING = "briefing"
    EMAIL_AND_CALENDAR = "email_and_calendar"
    COMPLEX = "complex"


def classify_intent(message: str) -> Intent:
    text = message.lower().strip()

    if re.search(r"\b(what time|time is it|current time|what'?s the time)\b", text):
        return Intent.TIME

    if re.search(
        r"\b(morning briefing|quick briefing|daily briefing|briefing|summarize my day)\b",
        text,
    ):
        return Intent.BRIEFING

    if _needs_email_and_calendar(text):
        return Intent.EMAIL_AND_CALENDAR

    if re.search(r"\b(unread|new emails|inbox)\b", text) and not _mentions_calendar(text):
        return Intent.UNREAD_EMAIL

    if _mentions_calendar(text) and re.search(
        r"\b(today|this morning|rest of (the )?day)\b", text
    ):
        return Intent.CALENDAR_TODAY

    if re.search(r"\b(calendar today|schedule today|meetings today)\b", text):
        return Intent.CALENDAR_TODAY

    return Intent.COMPLEX


def _mentions_calendar(text: str) -> bool:
    return bool(
        re.search(
            r"\b(calendar|schedule|meeting|meetings|free|available|afternoon)\b",
            text,
        )
    )


def _needs_email_and_calendar(text: str) -> bool:
    has_email = bool(
        re.search(r"\b(email|emails|inbox|manager|boss|from my)\b", text)
    )
    has_calendar = _mentions_calendar(text)
    return has_email and has_calendar
