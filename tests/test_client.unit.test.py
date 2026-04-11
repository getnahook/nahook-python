"""Unit tests for NahookClient.

Uses unittest.mock to patch httpx.Client and capture calls.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from nahook import NahookClient

API_KEY = "nhk_us_test123"
BASE_URL = "https://api.test.com"


def _make_response(body=None, status_code: int = 200) -> httpx.Response:
    """Build a fake httpx.Response."""
    content = json.dumps(body).encode() if body is not None else b""
    return httpx.Response(
        status_code=status_code,
        content=content,
        headers={"content-type": "application/json"},
    )


@pytest.fixture()
def mock_httpx_client():
    """Patch httpx.Client so no real HTTP calls are made.

    Yields a MagicMock instance representing the httpx.Client.
    Configure ``mock.request.return_value`` in each test.
    """
    with patch("nahook.http_client.httpx.Client") as MockClient:
        mock = MockClient.return_value
        mock.close = MagicMock()
        yield mock


# ── API key validation ──


class TestApiKeyValidation:
    def test_client_rejects_invalid_api_key(self):
        with pytest.raises(ValueError, match="must start with 'nhk_'"):
            NahookClient("bad_key")

    def test_client_rejects_nhm_prefix(self):
        with pytest.raises(ValueError, match="must start with 'nhk_'"):
            NahookClient("nhm_management_token")

    def test_client_accepts_valid_api_key(self, mock_httpx_client):
        client = NahookClient(API_KEY, base_url=BASE_URL)
        assert client is not None


# ── send() ──


class TestSend:
    def test_send_calls_correct_url(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_response(
            {"deliveryId": "del_1", "idempotencyKey": "k", "status": "accepted"}, 202
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        client.send("ep_abc", {"foo": "bar"})

        mock_httpx_client.request.assert_called_once()
        call_kwargs = mock_httpx_client.request.call_args
        assert call_kwargs.kwargs["method"] == "POST"
        assert call_kwargs.kwargs["url"] == f"{BASE_URL}/api/ingest/ep_abc"

    def test_send_auto_generates_idempotency_key(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_response(
            {"deliveryId": "del_1", "idempotencyKey": "k", "status": "accepted"}, 202
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        client.send("ep_abc", {"data": 1})

        call_kwargs = mock_httpx_client.request.call_args
        body = call_kwargs.kwargs["json"]
        assert "idempotencyKey" in body
        assert isinstance(body["idempotencyKey"], str)
        assert len(body["idempotencyKey"]) > 0

    def test_send_uses_provided_idempotency_key(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_response(
            {"deliveryId": "del_1", "idempotencyKey": "my-key", "status": "accepted"}, 202
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        client.send("ep_abc", {"data": 1}, idempotency_key="my-key")

        call_kwargs = mock_httpx_client.request.call_args
        body = call_kwargs.kwargs["json"]
        assert body["idempotencyKey"] == "my-key"


# ── trigger() ──


class TestTrigger:
    def test_trigger_calls_correct_url(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_response(
            {"eventTypeId": "evt_1", "deliveryIds": ["del_1"], "status": "accepted"}, 202
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        client.trigger("order.paid", {"orderId": "123"})

        call_kwargs = mock_httpx_client.request.call_args
        assert call_kwargs.kwargs["method"] == "POST"
        assert call_kwargs.kwargs["url"] == f"{BASE_URL}/api/ingest/event/order.paid"

    def test_trigger_has_no_idempotency_key(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_response(
            {"eventTypeId": "evt_1", "deliveryIds": [], "status": "accepted"}, 202
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        client.trigger("order.paid", {"orderId": "123"})

        call_kwargs = mock_httpx_client.request.call_args
        body = call_kwargs.kwargs["json"]
        assert "idempotencyKey" not in body


# ── send_batch() ──


class TestSendBatch:
    def test_send_batch_wraps_items(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_response(
            {"items": [{"index": 0, "deliveryId": "del_1", "status": "accepted"}]}, 202
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        items = [{"endpointId": "ep_1", "payload": {"x": 1}}]
        result = client.send_batch(items)

        call_kwargs = mock_httpx_client.request.call_args
        body = call_kwargs.kwargs["json"]
        assert "items" in body
        assert body["items"] == items
        assert result["items"][0]["status"] == "accepted"


# ── trigger_batch() ──


class TestTriggerBatch:
    def test_trigger_batch_wraps_items(self, mock_httpx_client):
        mock_httpx_client.request.return_value = _make_response(
            {"items": [{"index": 0, "eventTypeId": "evt_1", "deliveryIds": [], "status": "accepted"}]}, 202
        )
        client = NahookClient(API_KEY, base_url=BASE_URL)
        items = [{"eventType": "order.paid", "payload": {"orderId": "1"}}]
        result = client.trigger_batch(items)

        call_kwargs = mock_httpx_client.request.call_args
        body = call_kwargs.kwargs["json"]
        assert "items" in body
        assert body["items"] == items
        assert len(result["items"]) == 1


# ── Context manager & close ──


class TestLifecycle:
    def test_client_is_context_manager(self, mock_httpx_client):
        with NahookClient(API_KEY, base_url=BASE_URL) as client:
            assert client is not None
        # __exit__ should have called close, which calls httpx close
        mock_httpx_client.close.assert_called_once()

    def test_close_calls_httpx_close(self, mock_httpx_client):
        client = NahookClient(API_KEY, base_url=BASE_URL)
        client.close()
        mock_httpx_client.close.assert_called_once()
