import json
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional

from openai import OpenAI


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

    def run(self, task: str, prior_context: Optional[str] = None) -> str:
        messages: List[dict[str, Any]] = [{"role": "system", "content": self.system_prompt}]
        if prior_context:
            messages.append(
                {
                    "role": "user",
                    "content": f"Context passed from the supervisor or another agent:\n{prior_context}",
                }
            )
        messages.append({"role": "user", "content": task})

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
            )
            message = response.choices[0].message
            if not message:
                raise RuntimeError(f"{self.name}: no response from the language model.")

            messages.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return (message.content or "").strip() or "(No response)"

            for tool_call in message.tool_calls:
                if tool_call.type != "function":
                    continue
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        f"{self.name}: invalid tool arguments for {tool_call.function.name}"
                    ) from exc
                result = self.execute_tool(tool_call.function.name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )
