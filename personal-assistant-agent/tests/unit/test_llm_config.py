"""Unit tests for LLM provider detection."""

import os
from unittest.mock import patch

import pytest

from src.llm_config import _detect_provider, resolve_llm_settings


class TestDetectProvider:
    def test_explicit_ollama(self, metrics):
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=False):
            assert _detect_provider() == "ollama"

    def test_nvapi_key_detects_nvidia(self, metrics):
        env = {
            "LLM_PROVIDER": "",
            "OPENAI_API_KEY": "nvapi-test-key",
            "GROQ_API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            assert _detect_provider() == "nvidia"

    def test_no_keys_defaults_ollama(self, metrics):
        env = {
            "LLM_PROVIDER": "",
            "OPENAI_API_KEY": "",
            "API_KEY": "",
            "GROQ_API_KEY": "",
            "NVIDIA_API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            assert _detect_provider() == "ollama"


class TestResolveLlmSettings:
    def test_ollama_settings(self, metrics):
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "ollama", "OPENAI_MODEL": "llama3.1"},
            clear=False,
        ):
            settings = resolve_llm_settings()
        assert settings.provider == "ollama"
        assert settings.model == "llama3.1"
        assert settings.client is not None
