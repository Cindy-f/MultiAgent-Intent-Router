#!/usr/bin/env python3
"""Run live evaluation with real Ollama + Google (actual wall-clock timing)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.live_eval import run_live_eval
from tests.metrics import MetricsStore

RESULTS = ROOT / "tests" / "results" / "live_eval_summary.txt"


def main() -> None:
    print("Live evaluation — real LLM and APIs (no mocks)\n")
    MetricsStore.reset()
    results = run_live_eval()
    for r in results:
        MetricsStore.add(
            name=r.name,
            test_type="live",
            success=r.success,
            latency_ms=r.latency_ms,
            prompt_tokens=r.prompt_tokens,
            completion_tokens=r.completion_tokens,
            model=r.model,
            error=r.error,
            llm_calls=r.llm_calls,
            llm_latency_ms=r.llm_latency_ms,
            tool_latency_ms=r.tool_latency_ms,
        )
    table = MetricsStore.format_table()
    print("\n" + "=" * 72)
    print("LIVE EVAL SUMMARY")
    print("=" * 72)
    print(table)
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(table + "\n", encoding="utf-8")
    print(f"\nSaved: {RESULTS}")


if __name__ == "__main__":
    main()
