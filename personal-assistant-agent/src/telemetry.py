"""Real-time timing and token usage for live LLM / tool calls."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator, List, Optional

from openai import OpenAI


def timing_enabled() -> bool:
    return os.environ.get("DEBUG_TIMING", "1").lower() in ("1", "true", "yes")


@dataclass
class TimingEvent:
    kind: str
    agent: str
    label: str
    duration_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class RunTelemetry:
    events: List[TimingEvent] = field(default_factory=list)

    def reset(self) -> None:
        self.events = []

    @property
    def llm_call_count(self) -> int:
        return sum(1 for e in self.events if e.kind == "llm")

    @property
    def total_prompt_tokens(self) -> int:
        return sum(e.prompt_tokens for e in self.events)

    @property
    def total_completion_tokens(self) -> int:
        return sum(e.completion_tokens for e in self.events)

    @property
    def llm_latency_ms(self) -> float:
        return sum(e.duration_ms for e in self.events if e.kind == "llm")

    @property
    def tool_latency_ms(self) -> float:
        return sum(e.duration_ms for e in self.events if e.kind == "tool")

    def _usage_from_response(self, response: Any) -> tuple[int, int]:
        usage = getattr(response, "usage", None)
        if not usage:
            return 0, 0
        prompt = getattr(usage, "prompt_tokens", None)
        completion = getattr(usage, "completion_tokens", None)
        if prompt is None and hasattr(usage, "total_tokens"):
            return int(getattr(usage, "total_tokens", 0) or 0), 0
        return int(prompt or 0), int(completion or 0)

    def record_llm(
        self, agent: str, label: str, duration_ms: float, response: Any
    ) -> None:
        prompt_tok, completion_tok = self._usage_from_response(response)
        self.events.append(
            TimingEvent(
                kind="llm",
                agent=agent,
                label=label,
                duration_ms=duration_ms,
                prompt_tokens=prompt_tok,
                completion_tokens=completion_tok,
            )
        )
        if timing_enabled():
            print(
                f"[timing] {agent} LLM {label}: {duration_ms:.0f} ms "
                f"(tokens {prompt_tok}+{completion_tok})"
            )

    @contextmanager
    def tool(self, agent: str, name: str) -> Generator[None, None, None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.events.append(
                TimingEvent(
                    kind="tool",
                    agent=agent,
                    label=name,
                    duration_ms=duration_ms,
                )
            )
            if timing_enabled():
                print(f"[timing] {agent} tool {name}: {duration_ms:.0f} ms")


telemetry = RunTelemetry()


def chat_completion(
    client: OpenAI,
    *,
    agent: str,
    label: str,
    **kwargs: Any,
) -> Any:
    """Real OpenAI-compatible completion with timing (no mocking)."""
    start = time.perf_counter()
    response = client.chat.completions.create(**kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    telemetry.record_llm(agent, label, duration_ms, response)
    return response
