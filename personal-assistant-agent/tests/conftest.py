"""Pytest session summary for live test metrics."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.metrics import MetricsStore

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def pytest_sessionstart(session):
    MetricsStore.reset()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    if not MetricsStore.records:
        return
    table = MetricsStore.format_table()
    summary_path = RESULTS_DIR / "test_summary.txt"
    summary_path.write_text(table + "\n", encoding="utf-8")
    print("\n" + "=" * 72)
    print("TEST METRICS SUMMARY")
    print("=" * 72)
    print(table)
    print(f"\nFull report: {summary_path}")
