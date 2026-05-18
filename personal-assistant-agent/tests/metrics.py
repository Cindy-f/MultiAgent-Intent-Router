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
    "test-mock": (0.0, 0.0),
}


@dataclass
class TestRecord:
    name: str
    test_type: str
    success: bool
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = "test-mock"
    error: Optional[str] = None

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
        model: str = "test-mock",
        error: Optional[str] = None,
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
            )
        )

    @classmethod
    def format_table(cls) -> str:
        if not cls.records:
            return "No test metrics recorded."

        headers = (
            "Test",
            "Type",
            "OK",
            "Latency (ms)",
            "Prompt tok",
            "Completion tok",
            "Total tok",
            "Est. cost ($)",
        )
        rows: List[tuple[str, ...]] = []
        for r in cls.records:
            rows.append(
                (
                    r.name,
                    r.test_type,
                    "PASS" if r.success else "FAIL",
                    f"{r.latency_ms:.1f}",
                    str(r.prompt_tokens),
                    str(r.completion_tokens),
                    str(r.total_tokens),
                    f"{r.estimated_cost_usd:.6f}",
                )
            )

        passed = sum(1 for r in cls.records if r.success)
        total = len(cls.records)
        success_rate = (passed / total) * 100 if total else 0.0
        total_latency = sum(r.latency_ms for r in cls.records)
        total_prompt = sum(r.prompt_tokens for r in cls.records)
        total_completion = sum(r.completion_tokens for r in cls.records)
        total_cost = sum(r.estimated_cost_usd for r in cls.records)

        rows.append(
            (
                "— AGGREGATE —",
                "all",
                f"{passed}/{total} ({success_rate:.0f}%)",
                f"{total_latency:.1f}",
                str(total_prompt),
                str(total_completion),
                str(total_prompt + total_completion),
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
            f"Total LLM latency (sum of tests): {total_latency:.1f} ms",
            f"Total tokens: {total_prompt + total_completion} "
            f"(prompt {total_prompt}, completion {total_completion})",
            f"Estimated total cost: ${total_cost:.6f}",
        ]
        return "\n".join(lines)
