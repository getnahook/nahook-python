"""Negative / resilience tests for the Nahook Python SDK.

Tests error handling when the server returns malformed, empty, or unexpected
responses. Uses unittest.mock to patch httpx.Client.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from nahook import NahookClient, NahookManagement
from nahook.errors import NahookAPIError

API_KEY = "nhk_us_test123"
MGMT_TOKEN = "nhm_test123"
BASE_URL = "https://api.test.com"


def _make_raw_response(
    status_code: int, body: str, content_type: str = "application/json"
) -> httpx.Response:
    """Build a fake httpx.Response with raw bytes content."""
    return httpx.Response(
        status_code=status_code,
        content=body.encode("utf-8") if body else b"",
        headers={"content-type": content_type},
    )


@pytest.fixture()
def mock_httpx_client():
    """Patch httpx.Client so no real HTTP calls are made."""
    with patch("nahook.http_client.httpx.Client") as MockClient:
        mock = MockClient.return_value
        mock.close = MagicMock()
        yield mock


class TestNEG01MalformedJson:
    """NEG-01: Malformed JSON response on 200 should throw a parse error."""

    def test_malformed_json_throws(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_raw_response(
            200, "{invalid json!!!"
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        with pytest.raises(Exception):
            client.send("ep_abc", {"foo": "bar"})


class TestNEG02EmptyBodyOn200:
    """NEG-02: Empty body on 200 should throw a meaningful error."""

    def test_empty_body_200_throws(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_raw_response(200, "")
        client = NahookClient(API_KEY, base_url=BASE_URL)
        with pytest.raises(Exception):
            client.send("ep_abc", {"foo": "bar"})


class TestNEG03HtmlBodyOn5xx:
    """NEG-03: 5xx with HTML body should raise NahookAPIError with status and retryable."""

    def test_html_503_raises_api_error(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_raw_response(
            503,
            "<html><body>Service Unavailable</body></html>",
            content_type="text/html",
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        with pytest.raises(NahookAPIError) as exc_info:
            client.send("ep_abc", {"foo": "bar"})
        error = exc_info.value
        assert error.status == 503
        assert error.is_retryable


class TestNEG04EmptyBodyOn500:
    """NEG-04: Empty body on 500 should raise NahookAPIError."""

    def test_empty_body_500_raises_api_error(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_raw_response(500, "")
        client = NahookClient(API_KEY, base_url=BASE_URL)
        with pytest.raises(NahookAPIError) as exc_info:
            client.send("ep_abc", {"foo": "bar"})
        error = exc_info.value
        assert error.status == 500
        assert error.is_retryable


class TestNEG05UnknownExtraFields:
    """NEG-05: Unknown extra fields in response should be handled gracefully."""

    def test_extra_fields_succeed(self, mock_httpx_client):
        body = {
            "deliveryId": "del_1",
            "idempotencyKey": "k",
            "status": "accepted",
            "unknownField": "should_be_ignored",
            "nested": {"deep": True},
        }
        mock_httpx_client.request.return_value = _make_raw_response(
            202, json.dumps(body)
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        result = client.send("ep_abc", {"foo": "bar"})
        assert result["deliveryId"] == "del_1"
        assert result["status"] == "accepted"


class TestNEG06MissingExpectedFields:
    """NEG-06: Missing expected fields should be handled gracefully (no crash)."""

    def test_missing_fields_succeed(self, mock_httpx_client):
        # Minimal response with only deliveryId
        body = {"deliveryId": "del_1"}
        mock_httpx_client.request.return_value = _make_raw_response(
            202, json.dumps(body)
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        result = client.send("ep_abc", {"foo": "bar"})
        assert result["deliveryId"] == "del_1"
