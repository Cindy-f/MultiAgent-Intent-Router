import json
from typing import Any, List, Optional

from openai import OpenAI

from src.agents import CalendarAgent, EmailAgent, TimeAgent
from src.dates import local_iso_date, resolve_schedule_date
from src.fast_paths import try_fast_reply
from src.google_tools import DEFAULT_UNREAD_MAX
from src.specialists.calendar_specialist import CalendarSpecialist
from src.specialists.email_specialist import EmailSpecialist
from src.telemetry import chat_completion, telemetry
from src.tool_summaries import (
    compact_email_list,
    format_emails_for_llm,
    format_schedule_for_llm,
)

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor for a personal assistant.

**Fast tools (use these first for simple reads):**
- check_unread_emails — list unread Gmail (compact summary returned)
- fetch_daily_schedule — today's or a given day's calendar
- get_current_time — local clock (quote the display field)

**Specialists (only for complex search or reasoning):**
- delegate_to_email_agent — find a person/topic in mail, nuanced email tasks
- delegate_to_calendar_agent — availability reasoning that needs prior email context

Routing:
- Unread / calendar today / time → direct tools above, then answer in one reply
- Morning briefing → check_unread_emails + fetch_daily_schedule (same turn if possible), then summarize
- Complex multi-step (e.g. find manager in email then check afternoon) → direct tools first; delegate only if tools are not enough

Never invent inbox or calendar data."""

SUPERVISOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_unread_emails",
            "description": "Fetch unread Gmail (metadata only, fast).",
            "parameters": {
                "type": "object",
                "properties": {
                    "maxResults": {
                        "type": "number",
                        "description": f"Max emails (default {DEFAULT_UNREAD_MAX}).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_daily_schedule",
            "description": "Fetch calendar for one local day. Omit date for today.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Optional YYYY-MM-DD.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Current local time. Use display field for the user.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_email_agent",
            "description": "Complex Gmail search/summary (not for simple unread list).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "prior_context": {"type": "string"},
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_calendar_agent",
            "description": "Complex calendar reasoning with optional email context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "prior_context": {"type": "string"},
                },
                "required": ["task"],
            },
        },
    },
]


class SupervisorAgent:
    """Central router: fast paths, direct tools, or specialist delegation."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        email_specialist: EmailSpecialist,
        calendar_specialist: CalendarSpecialist,
        time_agent: TimeAgent,
        email_worker: EmailAgent,
        calendar_worker: CalendarAgent,
    ) -> None:
        self.client = client
        self.model = model
        self.email_specialist = email_specialist
        self.calendar_specialist = calendar_specialist
        self.time_agent = time_agent
        self.email_worker = email_worker
        self.calendar_worker = calendar_worker
        self.history: List[dict[str, Any]] = []

    def reset_session(self) -> None:
        self.history = []
        self.email_worker.clear_cache()
        self.calendar_worker.clear_cache()

    def chat(self, user_message: str) -> str:
        fast = try_fast_reply(
            client=self.client,
            model=self.model,
            message=user_message,
            email_worker=self.email_worker,
            calendar_worker=self.calendar_worker,
            time_agent=self.time_agent,
        )
        if fast is not None:
            return fast

        self.history.append({"role": "user", "content": user_message})
        tool_rounds = 0
        max_tool_rounds = 3

        while True:
            response = chat_completion(
                self.client,
                agent="supervisor",
                label=f"turn_{len(self.history)}",
                model=self.model,
                messages=[{"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT}]
                + self.history,
                tools=SUPERVISOR_TOOLS if tool_rounds < max_tool_rounds else None,
                tool_choice="auto" if tool_rounds < max_tool_rounds else None,
            )

            message = response.choices[0].message
            if not message:
                raise RuntimeError("Supervisor: no response from the language model.")

            self.history.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return (message.content or "(No response)").strip()

            tool_rounds += 1
            for tool_call in message.tool_calls:
                if tool_call.type != "function":
                    continue
                with telemetry.tool("supervisor", tool_call.function.name):
                    result = self._run_supervisor_tool(
                        tool_call.function.name,
                        tool_call.function.arguments or "{}",
                    )
                self.history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

    def _run_supervisor_tool(self, name: str, args_json: str) -> Any:
        try:
            args = json.loads(args_json) if args_json else {}
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Supervisor: invalid tool arguments for {name}") from exc

        if name == "check_unread_emails":
            max_results = args.get("maxResults", DEFAULT_UNREAD_MAX)
            if not isinstance(max_results, (int, float)):
                max_results = DEFAULT_UNREAD_MAX
            emails = self.email_worker.check_unread_emails(int(max_results))
            return {
                "count": len(emails),
                "summary": format_emails_for_llm(emails),
                "emails": compact_email_list(emails),
            }

        if name == "fetch_daily_schedule":
            date_str = resolve_schedule_date(args.get("date"))
            schedule = self.calendar_worker.fetch_daily_meeting_schedule(date_str)
            return {
                "summary": format_schedule_for_llm(schedule),
                "schedule": schedule.to_dict(),
            }

        if name == "get_current_time":
            return self.time_agent.get_current_time()

        if name == "delegate_to_email_agent":
            task = args.get("task")
            if not isinstance(task, str) or not task.strip():
                raise RuntimeError("delegate_to_email_agent requires a non-empty task")
            prior = args.get("prior_context")
            prior_str = prior if isinstance(prior, str) else None
            output = self.email_specialist.run(task.strip(), prior_str)
            return {"agent": "email", "output": output}

        if name == "delegate_to_calendar_agent":
            task = args.get("task")
            if not isinstance(task, str) or not task.strip():
                raise RuntimeError("delegate_to_calendar_agent requires a non-empty task")
            prior = args.get("prior_context")
            prior_str = prior if isinstance(prior, str) else None
            output = self.calendar_specialist.run(task.strip(), prior_str)
            return {"agent": "calendar", "output": output}

        raise RuntimeError(f"Supervisor: unknown tool {name}")
