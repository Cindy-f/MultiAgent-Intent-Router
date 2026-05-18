"""Unit tests for local date and timezone helpers."""

import os
from datetime import date
from unittest.mock import patch

import pytest

from src.dates import (
    local_day_bounds,
    local_iso_date,
    local_now_info,
    resolve_schedule_date,
)


class TestResolveScheduleDate:
    def test_valid_iso_date(self, metrics):
        assert resolve_schedule_date("2026-05-16") == "2026-05-16"

    def test_today_keyword(self, metrics):
        with patch("src.dates.local_iso_date", return_value="2026-05-16"):
            assert resolve_schedule_date("today") == "2026-05-16"

    def test_invalid_tool_name_defaults_to_today(self, metrics):
        with patch("src.dates.local_iso_date", return_value="2026-05-16"):
            assert resolve_schedule_date("get_current_time") == "2026-05-16"

    def test_none_defaults_to_today(self, metrics):
        with patch("src.dates.local_iso_date", return_value="2026-05-16"):
            assert resolve_schedule_date(None) == "2026-05-16"


class TestLocalDayBounds:
    def test_bounds_for_one_day(self, metrics):
        with patch.dict(os.environ, {"LOCAL_TIMEZONE": "America/Chicago"}):
            bounds = local_day_bounds("2026-05-16")
        assert "timeMin" in bounds
        assert "timeMax" in bounds
        assert bounds["timeMin"] < bounds["timeMax"]

    def test_invalid_date_raises(self, metrics):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            local_day_bounds("not-a-date")


class TestLocalNowInfo:
    def test_display_fields(self, metrics):
        with patch.dict(os.environ, {"LOCAL_TIMEZONE": "America/Chicago"}):
            info = local_now_info()
        assert "display" in info
        assert "timezone" in info
        assert info["timezone"] == "America/Chicago"
        assert "PM" in info["display"] or "AM" in info["display"]
