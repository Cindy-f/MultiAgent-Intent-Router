"""Collect per-test metrics and render a summary table."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# USD per 1M tokens (input, output) — estimates for reporting
MODEL_PRICING_PER_1M: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "llama3.1": (0.0, 0.0),
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "meta/llama-3.3-70b-instruct": (0.0, 0.0),
}


@dataclass
class TestRecord:
    name: str
    test_type: str
    success: bool
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""
    error: Optional[str] = None
    llm_calls: int = 0
    llm_latency_ms: float = 0.0
    tool_latency_ms: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def estimated_cost_usd(self) -> float:
        input_rate, output_rate = MODEL_PRICING_PER_1M.get(
            self.model, (0.0, 0.0)
        )
        return (
            self.prompt_tokens * input_rate / 1_000_000
            + self.completion_tokens * output_rate / 1_000_000
        )


@dataclass
class MetricsStore:
    records: List[TestRecord] = field(default_factory=list)

    @classmethod
    def reset(cls) -> None:
        cls.records = []

    @classmethod
    def add(
        cls,
        *,
        name: str,
        test_type: str,
        success: bool,
        latency_ms: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        model: str = "",
        error: Optional[str] = None,
        llm_calls: int = 0,
        llm_latency_ms: float = 0.0,
        tool_latency_ms: float = 0.0,
    ) -> None:
        cls.records.append(
            TestRecord(
                name=name,
                test_type=test_type,
                success=success,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model=model,
                error=error,
                llm_calls=llm_calls,
                llm_latency_ms=llm_latency_ms,
                tool_latency_ms=tool_latency_ms,
            )
        )

    @classmethod
    def format_table(cls) -> str:
        if not cls.records:
            return "No test metrics recorded."

        has_live = any(r.test_type == "live" for r in cls.records)
        headers = (
            "Test",
            "Type",
            "OK",
            "Wall (s)" if has_live else "Latency (ms)",
            "LLM calls",
            "LLM (s)",
            "Tools (s)",
            "Prompt tok",
            "Completion tok",
            "Est. cost ($)",
        )
        rows: List[tuple[str, ...]] = []
        for r in cls.records:
            wall = (
                f"{r.latency_ms / 1000:.1f}"
                if has_live
                else f"{r.latency_ms:.1f}"
            )
            rows.append(
                (
                    r.name,
                    r.test_type,
                    "PASS" if r.success else "FAIL",
                    wall,
                    str(r.llm_calls),
                    f"{r.llm_latency_ms / 1000:.1f}",
                    f"{r.tool_latency_ms / 1000:.1f}",
                    str(r.prompt_tokens),
                    str(r.completion_tokens),
                    f"{r.estimated_cost_usd:.6f}",
                )
            )

        passed = sum(1 for r in cls.records if r.success)
        total = len(cls.records)
        success_rate = (passed / total) * 100 if total else 0.0
        total_wall = sum(r.latency_ms for r in cls.records)
        total_llm_calls = sum(r.llm_calls for r in cls.records)
        total_llm_ms = sum(r.llm_latency_ms for r in cls.records)
        total_tool_ms = sum(r.tool_latency_ms for r in cls.records)
        total_prompt = sum(r.prompt_tokens for r in cls.records)
        total_completion = sum(r.completion_tokens for r in cls.records)
        total_cost = sum(r.estimated_cost_usd for r in cls.records)

        rows.append(
            (
                "— AGGREGATE —",
                "all",
                f"{passed}/{total} ({success_rate:.0f}%)",
                f"{total_wall / 1000:.1f}" if has_live else f"{total_wall:.1f}",
                str(total_llm_calls),
                f"{total_llm_ms / 1000:.1f}",
                f"{total_tool_ms / 1000:.1f}",
                str(total_prompt),
                str(total_completion),
                f"{total_cost:.6f}",
            )
        )

        col_widths = [
            max(len(headers[i]), max(len(row[i]) for row in rows))
            for i in range(len(headers))
        ]

        def fmt_row(cells: tuple[str, ...]) -> str:
            return " | ".join(cells[i].ljust(col_widths[i]) for i in range(len(cells)))

        sep = "-+-".join("-" * w for w in col_widths)
        lines = [
            fmt_row(headers),
            sep,
            *[fmt_row(row) for row in rows],
            "",
            f"Task success rate: {success_rate:.1f}% ({passed}/{total})",
        ]
        if has_live:
            lines.append(f"Total wall time: {total_wall / 1000:.1f} s")
            lines.append(f"Total LLM time: {total_llm_ms / 1000:.1f} s ({total_llm_calls} calls)")
            lines.append(f"Total tool/API time: {total_tool_ms / 1000:.1f} s")
        else:
            lines.append(f"Total latency (sum of tests): {total_wall:.1f} ms")
        lines.append(
            f"Total tokens: {total_prompt + total_completion} "
            f"(prompt {total_prompt}, completion {total_completion})"
        )
        lines.append(f"Estimated total cost: ${total_cost:.6f}")
        return "\n".join(lines)
