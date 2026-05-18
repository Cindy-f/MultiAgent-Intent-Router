"""Live tests — real Ollama + Google APIs, actual wall-clock timing (no mocks)."""

import pytest

from src.live_eval import google_configured, ollama_reachable
from tests.metrics import MetricsStore

pytestmark = pytest.mark.live


@pytest.fixture(scope="module", autouse=True)
def require_ollama():
    if not ollama_reachable():
        pytest.skip("Ollama not running at localhost:11434 — start with: brew services start ollama")


def test_live_eval_completed(live_results):
    assert len(MetricsStore.records) >= 1


def test_live_time_prompt(live_results):
    rec = next((r for r in MetricsStore.records if r.name == "time_now"), None)
    assert rec is not None
    assert rec.test_type == "live"
    if google_configured() or not rec.error:
        assert rec.latency_ms > 0


@pytest.mark.skipif(not google_configured(), reason="Google OAuth not in .env")
def test_live_calendar_prompt(live_results):
    rec = next((r for r in MetricsStore.records if r.name == "calendar_today"), None)
    assert rec is not None
    assert rec.success, rec.error or "calendar failed"


def test_live_summary_table(live_results):
    table = MetricsStore.format_table()
    assert "Task success rate" in table
    assert "Wall" in table or "wall" in table.lower()
