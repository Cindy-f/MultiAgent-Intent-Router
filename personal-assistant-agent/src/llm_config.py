import os
from dataclasses import dataclass
from typing import Any, Literal, Optional

from openai import OpenAI

LlmProvider = Literal["openai", "ollama", "groq", "nvidia"]

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"


@dataclass
class LlmSettings:
    provider: LlmProvider
    client: OpenAI
    model: str
    label: str


def _first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    return None


def _has_cloud_api_key() -> bool:
    key = _first_env("OPENAI_API_KEY", "API_KEY", "GROQ_API_KEY", "NVIDIA_API_KEY")
    if not key:
        return False
    lowered = key.lower()
    if "your_" in lowered or key.endswith("..."):
        return False
    return True


def _detect_provider() -> LlmProvider:
    explicit = (os.environ.get("LLM_PROVIDER") or "").lower()
    if explicit in ("ollama", "groq", "nvidia", "openai"):
        return explicit  # type: ignore[return-value]

    key = _first_env("OPENAI_API_KEY", "API_KEY", "GROQ_API_KEY", "NVIDIA_API_KEY")
    if key and key.startswith("nvapi-"):
        return "nvidia"
    if _first_env("GROQ_API_KEY"):
        return "groq"
    base = os.environ.get("OPENAI_BASE_URL") or ""
    if "11434" in base:
        return "ollama"

    if not _has_cloud_api_key():
        return "ollama"

    return "openai"


def _require_key(provider: str, *names: str) -> str:
    key = _first_env(*names)
    if not key:
        hint = (
            " Or set LLM_PROVIDER=ollama in .env to use free local Ollama (no API key)."
            if provider == "OpenAI"
            else ""
        )
        raise RuntimeError(
            f"Missing API key for {provider}. Set one of: {', '.join(names)} in .env.{hint}"
        )
    return key


def resolve_llm_settings() -> LlmSettings:
    provider = _detect_provider()

    if provider == "ollama":
        return LlmSettings(
            provider=provider,
            label="Ollama (local)",
            client=OpenAI(
                base_url=_first_env("OPENAI_BASE_URL") or OLLAMA_BASE_URL,
                api_key=_first_env("OPENAI_API_KEY") or "ollama",
            ),
            model=_first_env("OPENAI_MODEL") or "llama3.1",
        )

    if provider == "groq":
        return LlmSettings(
            provider=provider,
            label="Groq",
            client=OpenAI(
                base_url=_first_env("OPENAI_BASE_URL") or GROQ_BASE_URL,
                api_key=_require_key("Groq", "GROQ_API_KEY", "OPENAI_API_KEY", "API_KEY"),
            ),
            model=_first_env("OPENAI_MODEL") or "llama-3.3-70b-versatile",
        )

    if provider == "nvidia":
        return LlmSettings(
            provider=provider,
            label="NVIDIA NIM",
            client=OpenAI(
                base_url=_first_env("OPENAI_BASE_URL") or NVIDIA_BASE_URL,
                api_key=_require_key(
                    "NVIDIA NIM", "NVIDIA_API_KEY", "OPENAI_API_KEY", "API_KEY"
                ),
            ),
            model=_first_env("OPENAI_MODEL") or "meta/llama-3.3-70b-instruct",
        )

    base_url = _first_env("OPENAI_BASE_URL")
    api_key = _require_key("OpenAI", "OPENAI_API_KEY", "API_KEY")
    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return LlmSettings(
        provider="openai",
        label="OpenAI-compatible API" if base_url else "OpenAI",
        client=OpenAI(**kwargs),
        model=_first_env("OPENAI_MODEL") or "gpt-4o-mini",
    )
