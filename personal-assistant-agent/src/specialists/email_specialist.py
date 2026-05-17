from typing import Any, List

from src.agents import EmailAgent
from src.specialists.base import SpecialistAgent

EMAIL_SYSTEM_PROMPT = """You are the Email Specialist for a personal assistant.

Your only job is Gmail: unread messages, senders, subjects, and finding information in the inbox.
You do not access calendar or scheduling.

Guidelines:
- Use check_unread_emails when you need live inbox data.
- When asked to find a person or email address, scan from/subject/snippet fields and state the best match clearly.
- Return structured facts the supervisor can pass to other agents (names, email addresses, subjects).
- Be concise. If nothing matches, say so explicitly."""

EMAIL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_unread_emails",
            "description": "Fetch unread emails from Gmail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "maxResults": {
                        "type": "number",
                        "description": "Max emails to return (default 10).",
                    },
                },
            },
        },
    },
]


class EmailSpecialist(SpecialistAgent):
    name = "email"

    def __init__(self, client, model: str, email_worker: EmailAgent) -> None:
        super().__init__(client, model)
        self.email_worker = email_worker

    @property
    def system_prompt(self) -> str:
        return EMAIL_SYSTEM_PROMPT

    @property
    def tools(self) -> List[dict[str, Any]]:
        return EMAIL_TOOLS

    def execute_tool(self, name: str, args: dict[str, Any]) -> Any:
        if name == "check_unread_emails":
            max_results = args.get("maxResults")
            if not isinstance(max_results, (int, float)):
                max_results = 10
            return self.email_worker.check_unread_emails(int(max_results))
        raise RuntimeError(f"Email specialist: unknown tool {name}")
