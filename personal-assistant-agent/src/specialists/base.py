import json
import os
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from openai import OpenAI

from src.telemetry import chat_completion, telemetry

_MAX_SPECIALIST_TOOL_ROUNDS = int(os.environ.get("SPECIALIST_MAX_TOOL_ROUNDS", "1"))


class SpecialistAgent(ABC):
    """LLM sub-agent with its own system prompt and tool loop."""

    name: str = "specialist"

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        ...

    @property
    @abstractmethod
    def tools(self) -> List[dict[str, Any]]:
        ...

    @abstractmethod
    def execute_tool(self, name: str, args: dict[str, Any]) -> Any:
        ...

    def _compact_tool_content(self, result: Any) -> str:
        """Keep tool messages small for faster follow-up LLM calls."""
        if isinstance(result, dict) and "summary" in result:
            return json.dumps({"summary": result["summary"]})
        if isinstance(result, list) and result and isinstance(result[0], dict):
            from src.tool_summaries import compact_email_list

            return json.dumps(compact_email_list(result))
        text = json.dumps(result)
        max_chars = int(os.environ.get("TOOL_RESULT_MAX_CHARS", "4000"))
        if len(text) > max_chars:
            return text[: max_chars - 3] + "..."
        return text

    def run(self, task: str, prior_context: Optional[str] = None) -> str:
        messages: List[dict[str, Any]] = [{"role": "system", "content": self.system_prompt}]
        if prior_context:
            messages.append(
                {
                    "role": "user",
                    "content": f"Context from supervisor:\n{prior_context[:2000]}",
                }
            )
        messages.append({"role": "user", "content": task})

        tool_rounds = 0

        while True:
            use_tools = tool_rounds < _MAX_SPECIALIST_TOOL_ROUNDS
            response = chat_completion(
                self.client,
                agent=self.name,
                label=f"turn_{len(messages)}",
                model=self.model,
                messages=messages,
                tools=self.tools if use_tools else None,
                tool_choice="auto" if use_tools else None,
            )
            message = response.choices[0].message
            if not message:
                raise RuntimeError(f"{self.name}: no response from the language model.")

            messages.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return (message.content or "").strip() or "(No response)"

            tool_rounds += 1
            for tool_call in message.tool_calls:
                if tool_call.type != "function":
                    continue
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        f"{self.name}: invalid tool arguments for {tool_call.function.name}"
                    ) from exc
                with telemetry.tool(self.name, tool_call.function.name):
                    result = self.execute_tool(tool_call.function.name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": self._compact_tool_content(result),
                    }
                )
