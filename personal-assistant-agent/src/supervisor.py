import json
from typing import Any, List, Optional

from openai import OpenAI

from src.agents import TimeAgent
from src.specialists.calendar_specialist import CalendarSpecialist
from src.specialists.email_specialist import EmailSpecialist
from src.telemetry import chat_completion, telemetry

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor for a personal assistant with two specialist sub-agents:

1. **Email Agent** — Gmail only (unread mail, finding addresses, summarizing messages).
2. **Calendar Agent** — Google Calendar only (schedule, meetings, availability).

You do NOT call Gmail or Calendar APIs yourself. You analyze the user's request and delegate.

Routing rules:
- Email-only questions → delegate_to_email_agent
- Calendar-only questions → delegate_to_calendar_agent
- Questions needing both (e.g. "find X in email then check my schedule", morning briefing) → delegate in order; pass each agent's output as prior_context to the next
- Current time → get_current_time (returns local time; quote the display field verbatim)

For multi-step tasks:
1. Run the email agent first when email data is needed.
2. Pass its full result as prior_context to the calendar agent when scheduling context depends on email.
3. Synthesize a clear final answer for the user.

Never invent inbox or calendar data. Only report what specialists return."""

SUPERVISOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "delegate_to_email_agent",
            "description": "Hand off a Gmail-focused task to the Email Specialist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Clear instruction for the email agent.",
                    },
                    "prior_context": {
                        "type": "string",
                        "description": "Optional context from a prior step.",
                    },
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_calendar_agent",
            "description": "Hand off a calendar-focused task to the Calendar Specialist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Clear instruction for the calendar agent.",
                    },
                    "prior_context": {
                        "type": "string",
                        "description": "Optional context (e.g. email agent found an address).",
                    },
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get current local date/time. Response includes display (use this for the user), timezone, and iso.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


class SupervisorAgent:
    """Central router: user intent → specialist delegation → final reply."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        email_specialist: EmailSpecialist,
        calendar_specialist: CalendarSpecialist,
        time_agent: TimeAgent,
    ) -> None:
        self.client = client
        self.model = model
        self.email_specialist = email_specialist
        self.calendar_specialist = calendar_specialist
        self.time_agent = time_agent
        self.history: List[dict[str, Any]] = []

    def reset_session(self) -> None:
        self.history = []

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        while True:
            response = chat_completion(
                self.client,
                agent="supervisor",
                label=f"turn_{len(self.history)}",
                model=self.model,
                messages=[{"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT}]
                + self.history,
                tools=SUPERVISOR_TOOLS,
                tool_choice="auto",
            )

            message = response.choices[0].message
            if not message:
                raise RuntimeError("Supervisor: no response from the language model.")

            self.history.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return (message.content or "(No response)").strip()

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

        if name == "get_current_time":
            return self.time_agent.get_current_time()

        raise RuntimeError(f"Supervisor: unknown tool {name}")
