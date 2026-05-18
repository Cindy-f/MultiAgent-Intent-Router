"""Run live prompts against the real agent (Ollama + Google APIs)."""

from __future__ import annotations

import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv

from src.llm_config import resolve_llm_settings
from src.orchestrator import LlmCoordinator
from src.telemetry import telemetry


@dataclass
class LiveEvalResult:
    name: str
    success: bool
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    model: str
    error: Optional[str]
    llm_calls: int
    llm_latency_ms: float
    tool_latency_ms: float


@dataclass
class LivePrompt:
    name: str
    prompt: str
    needs_google: bool = True


DEFAULT_LIVE_PROMPTS: List[LivePrompt] = [
    LivePrompt("time_now", "What time is it now?", needs_google=False),
    LivePrompt("calendar_today", "What's on my calendar today?"),
    LivePrompt("unread_email", "What unread emails do I have?"),
    LivePrompt("morning_briefing", "Give me a quick morning briefing."),
    LivePrompt(
        "email_then_calendar",
        "Find emails from my manager and tell me if I'm free this afternoon.",
    ),
]


def ollama_reachable(base_url: Optional[str] = None) -> bool:
    url = (base_url or os.environ.get("OPENAI_BASE_URL") or "http://localhost:11434/v1").rstrip(
        "/"
    )
    if not url.endswith("/api/tags"):
        url = url.replace("/v1", "") + "/api/tags"
    try:
        urllib.request.urlopen(url, timeout=3)
        return True
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def google_configured() -> bool:
    client_id = os.environ.get("CLIENT_ID", "")
    return bool(client_id) and "your_client_id" not in client_id.lower()


def run_live_eval(
    prompts: Optional[List[LivePrompt]] = None,
    *,
    authenticate_google: bool = True,
) -> List[LiveEvalResult]:
    load_dotenv()
    telemetry.reset()
    results: List[LiveEvalResult] = []

    llm = resolve_llm_settings()
    if llm.provider == "ollama" and not ollama_reachable():
        raise RuntimeError(
            "Ollama is not reachable. Start it with: brew services start ollama"
        )

    coordinator = LlmCoordinator()
    if authenticate_google and google_configured():
        coordinator.authenticate()
    elif authenticate_google:
        print("Warning: Google credentials missing; skipping prompts that need Gmail/Calendar.")

    for case in prompts or DEFAULT_LIVE_PROMPTS:
        if case.needs_google and not google_configured():
            results.append(
                LiveEvalResult(
                    name=case.name,
                    success=False,
                    latency_ms=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    model=llm.model,
                    error="Google OAuth not configured in .env",
                    llm_calls=0,
                    llm_latency_ms=0,
                    tool_latency_ms=0,
                )
            )
            continue

        telemetry.reset()
        coordinator.reset_session()

        print(f"\n--- Live eval: {case.name} ---")
        print(f"Prompt: {case.prompt}")

        success = False
        error: Optional[str] = None
        reply = ""
        wall_start = time.perf_counter()

        try:
            reply = coordinator.chat(case.prompt)
            success = bool(reply and reply.strip() and reply != "(No response)")
            print(f"Reply ({len(reply)} chars): {reply[:200]}{'...' if len(reply) > 200 else ''}")
        except Exception as exc:
            error = str(exc)[:300]
            print(f"FAILED: {error}")

        wall_ms = (time.perf_counter() - wall_start) * 1000

        results.append(
            LiveEvalResult(
                name=case.name,
                success=success,
                latency_ms=wall_ms,
                prompt_tokens=telemetry.total_prompt_tokens,
                completion_tokens=telemetry.total_completion_tokens,
                model=llm.model,
                error=error,
                llm_calls=telemetry.llm_call_count,
                llm_latency_ms=telemetry.llm_latency_ms,
                tool_latency_ms=telemetry.tool_latency_ms,
            )
        )

    return results
