import json
import os
from dataclasses import dataclass
from typing import Any, List, Literal, Optional

from openai import OpenAI

from src.agents import CalendarAgent, EmailAgent, TimeAgent
from src.dates import local_iso_date
from src.google_auth import GoogleServicesUtils

# --- LLM provider configuration ---

LlmProvider = Literal["openai", "ollama", "groq", "nvidia"]

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"


@dataclass
class LlmSettings:
    provider: LlmProvider
    client: OpenAI
    model: str
    label: str


def _first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    return None


def _has_cloud_api_key() -> bool:
    key = _first_env("OPENAI_API_KEY", "API_KEY", "GROQ_API_KEY", "NVIDIA_API_KEY")
    if not key:
        return False
    lowered = key.lower()
    if "your_" in lowered or key.endswith("..."):
        return False
    return True


def _detect_provider() -> LlmProvider:
    explicit = (os.environ.get("LLM_PROVIDER") or "").lower()
    if explicit in ("ollama", "groq", "nvidia", "openai"):
        return explicit  # type: ignore[return-value]

    key = _first_env("OPENAI_API_KEY", "API_KEY", "GROQ_API_KEY", "NVIDIA_API_KEY")
    if key and key.startswith("nvapi-"):
        return "nvidia"
    if _first_env("GROQ_API_KEY"):
        return "groq"
    base = os.environ.get("OPENAI_BASE_URL") or ""
    if "11434" in base:
        return "ollama"

    if not _has_cloud_api_key():
        return "ollama"

    return "openai"


def _require_key(provider: str, *names: str) -> str:
    key = _first_env(*names)
    if not key:
        hint = (
            " Or set LLM_PROVIDER=ollama in .env to use free local Ollama (no API key)."
            if provider == "OpenAI"
            else ""
        )
        raise RuntimeError(
            f"Missing API key for {provider}. Set one of: {', '.join(names)} in .env.{hint}"
        )
    return key


def resolve_llm_settings() -> LlmSettings:
    provider = _detect_provider()

    if provider == "ollama":
        return LlmSettings(
            provider=provider,
            label="Ollama (local)",
            client=OpenAI(
                base_url=_first_env("OPENAI_BASE_URL") or OLLAMA_BASE_URL,
                api_key=_first_env("OPENAI_API_KEY") or "ollama",
            ),
            model=_first_env("OPENAI_MODEL") or "llama3.1",
        )

    if provider == "groq":
        return LlmSettings(
            provider=provider,
            label="Groq",
            client=OpenAI(
                base_url=_first_env("OPENAI_BASE_URL") or GROQ_BASE_URL,
                api_key=_require_key("Groq", "GROQ_API_KEY", "OPENAI_API_KEY", "API_KEY"),
            ),
            model=_first_env("OPENAI_MODEL") or "llama-3.3-70b-versatile",
        )

    if provider == "nvidia":
        return LlmSettings(
            provider=provider,
            label="NVIDIA NIM",
            client=OpenAI(
                base_url=_first_env("OPENAI_BASE_URL") or NVIDIA_BASE_URL,
                api_key=_require_key(
                    "NVIDIA NIM", "NVIDIA_API_KEY", "OPENAI_API_KEY", "API_KEY"
                ),
            ),
            model=_first_env("OPENAI_MODEL") or "meta/llama-3.3-70b-instruct",
        )

    base_url = _first_env("OPENAI_BASE_URL")
    api_key = _require_key("OpenAI", "OPENAI_API_KEY", "API_KEY")
    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return LlmSettings(
        provider="openai",
        label="OpenAI-compatible API" if base_url else "OpenAI",
        client=OpenAI(**kwargs),
        model=_first_env("OPENAI_MODEL") or "gpt-4o-mini",
    )


# --- LLM coordinator ---

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.events.readonly",
]

SYSTEM_PROMPT = """You are a personal assistant with access to the user's Gmail, Google Calendar, and system clock.

Use tools when the user asks about unread email, inbox, messages, calendar, meetings, schedule, or the current time.
Combine multiple tools when a question needs more than one data source (for example, "summarize my morning" may need email and calendar).

When presenting results:
- Be concise and readable.
- For emails, highlight sender and subject.
- For calendar events, show time windows and titles.
- Always call fetch_daily_schedule for calendar questions; never guess.
- fetch_daily_schedule returns { date, timeZone, events }. If events is empty, say no events for that date.
- For "today", omit the date argument so the tool uses the user's local today."""

COORDINATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_unread_emails",
            "description": "Fetch unread emails from the user Gmail inbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "maxResults": {
                        "type": "number",
                        "description": "Maximum number of emails to return (default 10).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_daily_schedule",
            "description": "Fetch Google Calendar events for one day in the user local timezone. Omit date for today.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Optional. Local calendar date YYYY-MM-DD. Leave empty for today.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current system time in ISO format.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


class LlmCoordinator:
    def __init__(self) -> None:
        llm = resolve_llm_settings()
        self.openai = llm.client
        self.model = llm.model
        self.llm_label = f"{llm.label} ({llm.model})"
        self.google = GoogleServicesUtils(
            os.environ.get("CLIENT_ID", ""),
            os.environ.get("CLIENT_SECRET", ""),
            os.environ.get("REDIRECT_URI", ""),
        )
        self.email_agent = EmailAgent(self.google)
        self.calendar_agent = CalendarAgent(self.google)
        self.time_agent = TimeAgent()
        self.history: List[dict[str, Any]] = []

    @property
    def email(self) -> EmailAgent:
        return self.email_agent

    @property
    def calendar(self) -> CalendarAgent:
        return self.calendar_agent

    @property
    def time(self) -> TimeAgent:
        return self.time_agent

    def authenticate(self) -> None:
        self.google.authenticate(GOOGLE_SCOPES)

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        while True:
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + self.history,
                tools=COORDINATOR_TOOLS,
                tool_choice="auto",
            )

            message = response.choices[0].message
            if not message:
                raise RuntimeError("No response from the language model.")

            self.history.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return (message.content or "(No response)").strip()

            for tool_call in message.tool_calls:
                if tool_call.type != "function":
                    continue
                result = self._run_tool(
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

    def _run_tool(self, name: str, args_json: str) -> Any:
        try:
            args = json.loads(args_json) if args_json else {}
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid tool arguments for {name}") from exc

        if name == "check_unread_emails":
            max_results = args.get("maxResults")
            if not isinstance(max_results, (int, float)):
                max_results = 10
            return self.email_agent.check_unread_emails(int(max_results))

        if name == "fetch_daily_schedule":
            date = args.get("date")
            if isinstance(date, str) and date.strip():
                date_str = date.strip()
            else:
                date_str = local_iso_date()
            schedule = self.calendar_agent.fetch_daily_meeting_schedule(date_str)
            return schedule.to_dict()

        if name == "get_current_time":
            return {"time": self.time_agent.get_current_time()}

        raise RuntimeError(f"Unknown tool: {name}")
