import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import BatchHttpRequest

from src.dates import local_day_bounds, local_iso_date, local_now_info, local_time_zone

DEFAULT_UNREAD_MAX = int(os.environ.get("GMAIL_MAX_RESULTS", "5"))
_SNIPPET_MAX = int(os.environ.get("EMAIL_SNIPPET_MAX_CHARS", "120"))


@dataclass
class CalendarEventSummary:
    summary: str
    time_window: str
    link: Optional[str] = None


@dataclass
class DailyScheduleResult:
    date: str
    time_zone: str
    events: List[CalendarEventSummary]

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "timeZone": self.time_zone,
            "events": [
                {
                    "summary": e.summary,
                    "timeWindow": e.time_window,
                    "link": e.link,
                }
                for e in self.events
            ],
        }


def get_current_time() -> dict[str, str]:
    return local_now_info()


def _truncate_snippet(snippet: str) -> str:
    text = (snippet or "").replace("\n", " ").strip()
    if len(text) <= _SNIPPET_MAX:
        return text
    return text[: _SNIPPET_MAX - 3] + "..."


def _header_value(headers: List[dict[str, Any]], name: str) -> str:
    for header in headers:
        if (header.get("name") or "").lower() == name.lower():
            return header.get("value") or "Unknown"
    return "Unknown"


def _parse_metadata_message(message: dict[str, Any]) -> dict[str, Any]:
    headers = (message.get("payload") or {}).get("headers") or []
    return {
        "id": message.get("id"),
        "from": _header_value(headers, "From"),
        "subject": _header_value(headers, "Subject"),
        "date": _header_value(headers, "Date"),
        "snippet": _truncate_snippet(message.get("snippet") or ""),
    }


def _batch_fetch_messages(gmail: Any, message_ids: List[str]) -> List[dict[str, Any]]:
    if not message_ids:
        return []

    by_id: dict[str, dict[str, Any]] = {}
    errors: List[str] = []

    def _callback(request_id: str, response: Any, exception: Optional[Exception]) -> None:
        if exception is not None:
            errors.append(str(exception))
            return
        if response:
            by_id[request_id] = _parse_metadata_message(response)

    batch: BatchHttpRequest = gmail.new_batch_http_request(callback=_callback)
    for mid in message_ids:
        batch.add(
            gmail.users().messages().get(
                userId="me",
                id=mid,
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ),
            request_id=mid,
        )
    batch.execute()

    if errors and not by_id:
        raise RuntimeError(f"Gmail batch fetch failed: {errors[0]}")

    return [by_id[mid] for mid in message_ids if mid in by_id]


def get_unread_emails(
    auth: Credentials, max_results: int = DEFAULT_UNREAD_MAX
) -> List[dict[str, Any]]:
    """Fetch unread mail using one list call + batched metadata gets."""
    gmail = build("gmail", "v1", credentials=auth)
    limit = max(1, min(int(max_results), 20))

    response = (
        gmail.users()
        .messages()
        .list(userId="me", q="is:unread", maxResults=limit)
        .execute()
    )

    message_refs = response.get("messages") or []
    ids = [m["id"] for m in message_refs if m and m.get("id")]
    return _batch_fetch_messages(gmail, ids)


def _format_event_time(iso_or_date: str) -> str:
    if "T" not in iso_or_date:
        return "All day"
    normalized = iso_or_date.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo:
        dt = dt.astimezone()
    return dt.strftime("%I:%M %p").lstrip("0") or dt.strftime("%I:%M %p")


def fetch_daily_meeting_schedule(
    auth: Credentials, date: Optional[str] = None
) -> DailyScheduleResult:
    calendar = build("calendar", "v3", credentials=auth)
    time_zone = local_time_zone()
    day = date or local_iso_date()
    bounds = local_day_bounds(day)

    response = (
        calendar.events()
        .list(
            calendarId="primary",
            timeMin=bounds["timeMin"],
            timeMax=bounds["timeMax"],
            timeZone=time_zone,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = response.get("items") or []
    mapped: List[CalendarEventSummary] = []

    for event in events:
        start_raw = (event.get("start") or {}).get("dateTime") or (event.get("start") or {}).get(
            "date"
        ) or ""
        end_raw = (event.get("end") or {}).get("dateTime") or (event.get("end") or {}).get(
            "date"
        ) or ""

        start_label = _format_event_time(start_raw)
        end_label = _format_event_time(end_raw) if "T" in end_raw else ""

        mapped.append(
            CalendarEventSummary(
                summary=event.get("summary") or "Untitled Event",
                time_window=f"{start_label} – {end_label}" if end_label else start_label,
                link=event.get("htmlLink"),
            )
        )

    return DailyScheduleResult(date=day, time_zone=time_zone, events=mapped)
