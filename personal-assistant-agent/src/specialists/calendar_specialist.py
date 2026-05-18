from typing import Any, List

from src.agents import CalendarAgent
from src.dates import resolve_schedule_date
from src.specialists.base import SpecialistAgent
from src.tool_summaries import format_schedule_for_llm

CALENDAR_SYSTEM_PROMPT = """You are the Calendar Specialist for a personal assistant.

Your only job is Google Calendar: daily schedules, meetings, and availability.
You do not read email.

Guidelines:
- Use fetch_daily_schedule for calendar data. Omit date or use YYYY-MM-DD only.
- When prior context includes an email address, meeting topic, or attendee from another agent, use it in your answer.
- This app has read-only calendar access: you can report events and suggest times, not create events on the calendar.
- Be concise. If there are no events, say so for the requested date."""

CALENDAR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_daily_schedule",
            "description": "Fetch calendar events for one local day. Omit date for today.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Optional YYYY-MM-DD. Empty means today.",
                    },
                },
            },
        },
    },
]


class CalendarSpecialist(SpecialistAgent):
    name = "calendar"

    def __init__(self, client, model: str, calendar_worker: CalendarAgent) -> None:
        super().__init__(client, model)
        self.calendar_worker = calendar_worker

    @property
    def system_prompt(self) -> str:
        return CALENDAR_SYSTEM_PROMPT

    @property
    def tools(self) -> List[dict[str, Any]]:
        return CALENDAR_TOOLS

    def execute_tool(self, name: str, args: dict[str, Any]) -> Any:
        if name == "fetch_daily_schedule":
            date_str = resolve_schedule_date(args.get("date"))
            schedule = self.calendar_worker.fetch_daily_meeting_schedule(date_str)
            return {
                "summary": format_schedule_for_llm(schedule),
                "schedule": schedule.to_dict(),
            }
        raise RuntimeError(f"Calendar specialist: unknown tool {name}")
