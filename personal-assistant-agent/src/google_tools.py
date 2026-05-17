from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.dates import local_day_bounds, local_time_zone


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


def get_current_time() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_unread_emails(auth: Credentials, max_results: int) -> List[dict[str, Any]]:
    gmail = build("gmail", "v1", credentials=auth)

    response = (
        gmail.users()
        .messages()
        .list(userId="me", q="is:unread", maxResults=max_results)
        .execute()
    )

    messages = response.get("messages") or []
    emails: List[dict[str, Any]] = []

    for message in messages:
        if not message or not message.get("id"):
            continue
        email_response = (
            gmail.users()
            .messages()
            .get(userId="me", id=message["id"])
            .execute()
        )
        headers = (email_response.get("payload") or {}).get("headers") or []

        def get_header(name: str) -> str:
            for h in headers:
                if (h.get("name") or "").lower() == name.lower():
                    return h.get("value") or "Unknown"
            return "Unknown"

        emails.append(
            {
                "id": email_response.get("id"),
                "from": get_header("From"),
                "subject": get_header("Subject"),
                "date": get_header("Date"),
                "snippet": email_response.get("snippet"),
            }
        )

    return emails


def _format_event_time(iso_or_date: str) -> str:
    if "T" not in iso_or_date:
        return "All day"
    normalized = iso_or_date.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo:
        dt = dt.astimezone()
    return dt.strftime("%I:%M %p").lstrip("0") or dt.strftime("%I:%M %p")


def fetch_daily_meeting_schedule(auth: Credentials, date: str) -> DailyScheduleResult:
    calendar = build("calendar", "v3", credentials=auth)
    time_zone = local_time_zone()
    bounds = local_day_bounds(date)

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

    return DailyScheduleResult(date=date, time_zone=time_zone, events=mapped)
