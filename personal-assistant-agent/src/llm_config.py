import os
from dataclasses import dataclass
from typing import Any, Literal, Optional
from urllib.parse import urlparse

from openai import OpenAI

LlmProvider = Literal["openai", "ollama", "groq", "nvidia"]

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

OLLAMA_FAST_MODEL = "llama3.2:3b"
GROQ_FAST_MODEL = "llama-3.1-8b-instant"


@dataclass
class LlmSettings:
    provider: LlmProvider
    client: OpenAI
    model: str
    label: str
    base_url: str


def _first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    return None


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return (
        "your_" in lowered
        or "_here" in lowered
        or lowered.endswith("...")
        or lowered in ("changeme", "placeholder", "xxx")
    )


def _is_valid_api_key(key: str, provider: LlmProvider) -> bool:
    if not key or _is_placeholder(key):
        return False
    if provider == "groq":
        return key.startswith("gsk_") and len(key) > 20
    if provider == "nvidia":
        return key.startswith("nvapi-") and len(key) > 20
    if provider == "openai":
        return key.startswith("sk-") and len(key) > 20
    return True


def _detect_provider() -> LlmProvider:
    explicit = (os.environ.get("LLM_PROVIDER") or "").lower().strip()
    if explicit in ("ollama", "groq", "nvidia", "openai"):
        return explicit  # type: ignore[return-value]

    groq_key = _first_env("GROQ_API_KEY")
    if groq_key and _is_valid_api_key(groq_key, "groq"):
        return "groq"

    key = _first_env("OPENAI_API_KEY", "API_KEY", "NVIDIA_API_KEY")
    if key and key.startswith("nvapi-") and _is_valid_api_key(key, "nvidia"):
        return "nvidia"
    if key and key.startswith("sk-") and _is_valid_api_key(key, "openai"):
        return "openai"

    base = os.environ.get("OPENAI_BASE_URL") or ""
    if "11434" in base:
        return "ollama"

    return "ollama"


def _base_url_for(provider: LlmProvider) -> str:
    """
    Use OPENAI_BASE_URL only when it matches the chosen provider.
    Prevents LLM_PROVIDER=ollama + OPENAI_BASE_URL=groq → 401 Invalid API Key.
    """
    override = _first_env("OPENAI_BASE_URL")
    dedicated = _first_env(
        "OLLAMA_BASE_URL" if provider == "ollama" else "",
        "GROQ_BASE_URL" if provider == "groq" else "",
        "NVIDIA_BASE_URL" if provider == "nvidia" else "",
    )

    if dedicated:
        return dedicated.rstrip("/")

    if override:
        host = urlparse(override).netloc.lower()
        if provider == "ollama" and ("11434" in override or "localhost" in host):
            return override.rstrip("/")
        if provider == "groq" and "groq.com" in host:
            return override.rstrip("/")
        if provider == "nvidia" and "nvidia.com" in host:
            return override.rstrip("/")
        if provider == "openai" and "groq.com" not in host and "11434" not in override:
            return override.rstrip("/")

    if provider == "ollama":
        return OLLAMA_BASE_URL
    if provider == "groq":
        return GROQ_BASE_URL
    if provider == "nvidia":
        return NVIDIA_BASE_URL
    return "https://api.openai.com/v1"


def _api_key_for(provider: LlmProvider) -> str:
    if provider == "ollama":
        return _first_env("OLLAMA_API_KEY") or "ollama"

    if provider == "groq":
        key = _first_env("GROQ_API_KEY")
        if key and _is_valid_api_key(key, "groq"):
            return key
        fallback = _first_env("OPENAI_API_KEY", "API_KEY")
        if fallback and fallback.startswith("gsk_") and _is_valid_api_key(fallback, "groq"):
            return fallback
        raise RuntimeError(
            "Groq requires a valid GROQ_API_KEY (starts with gsk_). "
            "Or set LLM_PROVIDER=ollama in .env for free local Ollama."
        )

    if provider == "nvidia":
        key = _first_env("NVIDIA_API_KEY", "OPENAI_API_KEY", "API_KEY")
        if key and _is_valid_api_key(key, "nvidia"):
            return key
        raise RuntimeError(
            "NVIDIA NIM requires NVIDIA_API_KEY (starts with nvapi-). "
            "Or set LLM_PROVIDER=ollama in .env."
        )

    key = _first_env("OPENAI_API_KEY", "API_KEY")
    if not key or not _is_valid_api_key(key, "openai"):
        raise RuntimeError(
            "OpenAI requires OPENAI_API_KEY (starts with sk-). "
            "Or set LLM_PROVIDER=ollama in .env for free local Ollama."
        )
    return key


def _default_model(provider: LlmProvider) -> str:
    override = _first_env("OPENAI_MODEL", "FAST_LLM_MODEL")
    if override:
        return override
    if provider == "ollama":
        return OLLAMA_FAST_MODEL
    if provider == "groq":
        return GROQ_FAST_MODEL
    if provider == "nvidia":
        return "meta/llama-3.3-70b-instruct"
    return "gpt-4o-mini"


def resolve_llm_settings() -> LlmSettings:
    provider = _detect_provider()
    model = _default_model(provider)
    base_url = _base_url_for(provider)
    api_key = _api_key_for(provider)

    labels = {
        "ollama": "Ollama (local)",
        "groq": "Groq",
        "nvidia": "NVIDIA NIM",
        "openai": "OpenAI",
    }
    client = OpenAI(base_url=base_url, api_key=api_key)

    return LlmSettings(
        provider=provider,
        label=labels[provider],
        client=client,
        model=model,
        base_url=base_url,
    )


def describe_llm_settings(settings: LlmSettings) -> str:
    """Safe one-line summary for logs (no secrets)."""
    host = urlparse(settings.base_url).netloc or settings.base_url
    return f"{settings.label} · model={settings.model} · host={host}"


def augment_llm_auth_error(message: str, settings: LlmSettings) -> str:
    """Append troubleshooting hints for 401 / invalid API key errors."""
    lower = message.lower()
    if "401" not in message and "invalid api key" not in lower:
        return message
    hint = (
        " Hint: Set LLM_PROVIDER in .env to match your backend (ollama | groq | openai). "
        "Remove OPENAI_BASE_URL if it points at the wrong host (e.g. api.groq.com while using Ollama). "
        "For local Ollama: brew services start ollama && ollama pull llama3.2:3b"
    )
    if settings.provider == "groq":
        hint = (
            " Hint: Groq needs a valid GROQ_API_KEY (gsk_...) and LLM_PROVIDER=groq. "
            "Or switch to Ollama: LLM_PROVIDER=ollama and remove Groq OPENAI_BASE_URL."
        )
    return message + hint
