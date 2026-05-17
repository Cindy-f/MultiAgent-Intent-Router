"""Backward compatibility: prefer `from src.orchestrator import LlmCoordinator`."""

from src.orchestrator import GOOGLE_SCOPES, LlmCoordinator

__all__ = ["LlmCoordinator", "GOOGLE_SCOPES"]
