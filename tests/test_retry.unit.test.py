"""Unit tests for retry delay calculation via _calculate_delay."""

from __future__ import annotations

import pytest

from nahook.http_client import BASE_DELAY_MS, MAX_DELAY_MS, _calculate_delay


class TestCalculateDelay:
    def test_delay_within_exponential_cap(self):
        """Returned delay is between 0 and (2^attempt * BASE_DELAY_MS)."""
        for attempt in range(5):
            cap = BASE_DELAY_MS * (2 ** attempt)
            for _ in range(50):
                delay = _calculate_delay(attempt)
                assert 0 <= delay <= cap

    def test_delay_caps_at_max_delay(self):
        """Even at high attempt numbers, delay never exceeds MAX_DELAY_MS."""
        for _ in range(100):
            delay = _calculate_delay(20)
            assert 0 <= delay <= MAX_DELAY_MS

    def test_uses_retry_after_when_provided(self):
        """When retry_after_ms is given, it is returned directly."""
        delay = _calculate_delay(0, retry_after_ms=7500.0)
        assert delay == 7500.0

        delay = _calculate_delay(5, retry_after_ms=3000.0)
        assert delay == 3000.0
