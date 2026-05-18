"""Pytest fixtures and session summary for test metrics."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tests.metrics import MetricsStore

RESULTS_DIR = Path(__file__).resolve().parent / "results"


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture
def metrics(request):
    """Track success, latency, and optional token counts per test."""
    ctx = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "model": "test-mock",
        "test_type": "integration" if "integration" in str(request.fspath) else "unit",
    }
    start = time.perf_counter()
    error: str | None = None
    success = True

    yield ctx

    latency_ms = (time.perf_counter() - start) * 1000
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        success = False
        if request.node.rep_call.longrepr:
            error = str(request.node.rep_call.longrepr)[:200]

    MetricsStore.add(
        name=request.node.name,
        test_type=ctx["test_type"],
        success=success,
        latency_ms=latency_ms,
        prompt_tokens=int(ctx.get("prompt_tokens", 0)),
        completion_tokens=int(ctx.get("completion_tokens", 0)),
        model=str(ctx.get("model", "test-mock")),
        error=error,
    )


def pytest_sessionstart(session):
    MetricsStore.reset()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    table = MetricsStore.format_table()
    summary_path = RESULTS_DIR / "test_summary.txt"
    summary_path.write_text(table + "\n", encoding="utf-8")
    print("\n" + "=" * 72)
    print("TEST METRICS SUMMARY")
    print("=" * 72)
    print(table)
    print(f"\nFull report: {summary_path}")
