"""Unit tests for regional routing via _resolve_base_url."""

from __future__ import annotations

import pytest

from nahook.http_client import DEFAULT_BASE_URL, _resolve_base_url


class TestResolveBaseUrl:
    def test_resolves_us_region(self):
        url = _resolve_base_url("nhk_us_abc123def456")
        assert url == "https://us.api.nahook.com"

    def test_resolves_eu_region(self):
        url = _resolve_base_url("nhk_eu_abc123def456")
        assert url == "https://eu.api.nahook.com"

    def test_resolves_ap_region(self):
        url = _resolve_base_url("nhk_ap_abc123def456")
        assert url == "https://ap.api.nahook.com"

    def test_falls_back_for_unknown_region(self):
        url = _resolve_base_url("nhk_zz_abc123def456")
        assert url == DEFAULT_BASE_URL

    def test_base_url_parameter_overrides_region(self):
        """When base_url is explicitly provided to HttpClient, it takes precedence."""
        from nahook.http_client import HttpClient
        from unittest.mock import patch

        with patch("nahook.http_client.httpx.Client"):
            client = HttpClient(
                token="nhk_eu_abc123def456",
                base_url="https://custom.example.com",
            )
            assert client._base_url == "https://custom.example.com"
