"""Short-lived in-memory cache for Google API reads within a chat session."""

from __future__ import annotations

import os
import time
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")

_DEFAULT_TTL = int(os.environ.get("GOOGLE_CACHE_TTL_SEC", "60"))


class TimedCache(Generic[T]):
    def __init__(self, ttl_sec: int = _DEFAULT_TTL) -> None:
        self.ttl_sec = ttl_sec
        self._value: Optional[T] = None
        self._expires_at: float = 0.0

    def get(self) -> Optional[T]:
        if self._value is not None and time.monotonic() < self._expires_at:
            return self._value
        return None

    def set(self, value: T) -> None:
        self._value = value
        self._expires_at = time.monotonic() + self.ttl_sec

    def clear(self) -> None:
        self._value = None
        self._expires_at = 0.0
