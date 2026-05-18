"""Load live eval results into MetricsStore for pytest reporting."""

from __future__ import annotations

import pytest

from src.live_eval import run_live_eval
from tests.metrics import MetricsStore


@pytest.fixture(scope="module")
def live_results():
    """One shared live run per pytest session (slow, real APIs)."""
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
    return results
