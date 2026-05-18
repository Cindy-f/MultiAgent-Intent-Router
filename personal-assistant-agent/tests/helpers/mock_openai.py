"""Mock OpenAI client for integration tests with token and latency tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional
from unittest.mock import MagicMock


@dataclass
class MockUsage:
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class MockLLMResponse:
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    usage: Optional[MockUsage] = None

    def model_dump(self, exclude_none: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {"role": "assistant"}
        if self.content is not None:
            data["content"] = self.content
        if self.tool_calls:
            data["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in self.tool_calls
            ]
        return data


def make_tool_call(
    name: str,
    arguments: str = "{}",
    call_id: str = "call_test_1",
) -> MagicMock:
    tc = MagicMock()
    tc.type = "function"
    tc.id = call_id
    tc.function = MagicMock()
    tc.function.name = name
    tc.function.arguments = arguments
    return tc


@dataclass
class MockOpenAIClient:
    """Queues LLM responses and records usage per completion call."""

    responses: List[MockLLMResponse] = field(default_factory=list)
    call_count: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_latency_ms: float = 0.0
    simulated_latency_ms: float = 5.0

    def completions_create(self, **kwargs: Any) -> MagicMock:
        if self.call_count >= len(self.responses):
            raise RuntimeError(
                f"MockOpenAIClient: no response queued for call #{self.call_count + 1}"
            )

        start = time.perf_counter()
        if self.simulated_latency_ms > 0:
            time.sleep(self.simulated_latency_ms / 1000.0)
        elapsed_ms = (time.perf_counter() - start) * 1000

        spec = self.responses[self.call_count]
        self.call_count += 1

        usage = spec.usage or MockUsage(prompt_tokens=50, completion_tokens=25)
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        self.total_latency_ms += elapsed_ms

        message = MagicMock()
        message.content = spec.content
        message.tool_calls = spec.tool_calls or []
        message.model_dump = lambda exclude_none=True: spec.model_dump(exclude_none)

        choice = MagicMock()
        choice.message = message

        result = MagicMock()
        result.choices = [choice]
        result.usage = usage
        return result

    def as_openai_client(self) -> MagicMock:
        client = MagicMock()
        client.chat.completions.create = self.completions_create
        return client
