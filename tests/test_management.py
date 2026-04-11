"""Tests for NahookManagement and all resource classes.

Mirrors the Node SDK test suite using pytest and httpx mocking.
"""

from __future__ import annotations

import json

import httpx
import pytest

from nahook import NahookClient, NahookManagement
from nahook.errors import NahookAPIError

TOKEN = "nhm_test123"
BASE_URL = "https://api.test.com"


# ── Helpers ──


def _mock_response(
    body=None, status_code: int = 200
) -> httpx.Response:
    content = json.dumps(body).encode() if body is not None else b""
    return httpx.Response(
        status_code=status_code,
        content=content,
        headers={"content-type": "application/json"},
    )


def _last_request(transport: _RecordingTransport) -> httpx.Request:
    assert transport.requests, "No requests were recorded"
    return transport.requests[-1]


class _RecordingTransport(httpx.BaseTransport):
    """Records requests and returns a preset response."""

    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._response


@pytest.fixture()
def _patch_client(monkeypatch):
    """Returns a helper that patches HttpClient._fetch to use a recording transport."""
    def _factory(body=None, status_code: int = 200):
        resp = _mock_response(body, status_code)
        transport = _RecordingTransport(resp)

        def patched_fetch(self, method, url, headers, body_data):
            # Build request without json= so httpx doesn't inject its own Content-Type.
            # We test Content-Type via the headers dict passed from _execute_with_retry.
            if body_data is not None:
                request = httpx.Request(
                    method, url, headers=headers,
                    content=json.dumps(body_data).encode(),
                )
            else:
                request = httpx.Request(method, url, headers=headers)
            transport.requests.append(request)
            return resp

        from nahook.http_client import HttpClient
        monkeypatch.setattr(HttpClient, "_fetch", patched_fetch)
        return transport

    return _factory


# ── Token validation ──


class TestTokenValidation:
    def test_rejects_invalid_management_token(self):
        with pytest.raises(ValueError, match="must start with 'nhm_'"):
            NahookManagement("bad_token")

    def test_accepts_valid_management_token(self):
        mgmt = NahookManagement(TOKEN)
        assert mgmt.endpoints is not None
        assert mgmt.event_types is not None
        assert mgmt.applications is not None
        assert mgmt.subscriptions is not None
        assert mgmt.portal_sessions is not None

    def test_rejects_invalid_client_key(self):
        with pytest.raises(ValueError, match="must start with 'nhk_'"):
            NahookClient("bad_key")

    def test_accepts_valid_client_key(self):
        client = NahookClient("nhk_us_test123")
        assert client is not None


# ── Endpoints ──


class TestEndpoints:
    def test_list_sends_get_to_endpoints(self, _patch_client):
        transport = _patch_client([{"id": "ep_1", "url": "https://example.com"}])
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.endpoints.list("ws_abc")
        req = _last_request(transport)
        assert req.method == "GET"
        assert str(req.url) == "https://api.test.com/management/v1/workspaces/ws_abc/endpoints"
        assert len(result["data"]) == 1

    def test_create_sends_post_with_body(self, _patch_client):
        transport = _patch_client({"id": "ep_new", "url": "https://example.com"}, 201)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.endpoints.create("ws_abc", url="https://example.com", description="Test")
        req = _last_request(transport)
        assert req.method == "POST"
        assert "/endpoints" in str(req.url)
        body = json.loads(req.content)
        assert body["url"] == "https://example.com"
        assert body["description"] == "Test"

    def test_get_sends_get_to_endpoint_id(self, _patch_client):
        transport = _patch_client({"id": "ep_1"})
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.endpoints.get("ws_abc", "ep_1")
        req = _last_request(transport)
        assert req.method == "GET"
        assert str(req.url) == "https://api.test.com/management/v1/workspaces/ws_abc/endpoints/ep_1"

    def test_update_sends_patch_with_body(self, _patch_client):
        transport = _patch_client({"id": "ep_1", "description": "Updated"})
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.endpoints.update("ws_abc", "ep_1", description="Updated")
        req = _last_request(transport)
        assert req.method == "PATCH"
        assert "/endpoints/ep_1" in str(req.url)
        body = json.loads(req.content)
        assert body["description"] == "Updated"

    def test_delete_sends_delete(self, _patch_client):
        transport = _patch_client(None, 204)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.endpoints.delete("ws_abc", "ep_1")
        req = _last_request(transport)
        assert req.method == "DELETE"
        assert "/endpoints/ep_1" in str(req.url)


# ── Event Types ──


class TestEventTypes:
    def test_list_sends_get_to_event_types(self, _patch_client):
        transport = _patch_client([{"id": "evt_1", "name": "order.paid"}])
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.event_types.list("ws_abc")
        req = _last_request(transport)
        assert req.method == "GET"
        assert str(req.url) == "https://api.test.com/management/v1/workspaces/ws_abc/event-types"
        assert len(result["data"]) == 1

    def test_create_sends_post_with_body(self, _patch_client):
        transport = _patch_client({"id": "evt_new", "name": "order.paid"}, 201)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.event_types.create("ws_abc", name="order.paid", description="Paid")
        req = _last_request(transport)
        assert req.method == "POST"
        assert "/event-types" in str(req.url)
        body = json.loads(req.content)
        assert body["name"] == "order.paid"

    def test_get_sends_get_to_event_type_id(self, _patch_client):
        transport = _patch_client({"id": "evt_1"})
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.event_types.get("ws_abc", "evt_1")
        req = _last_request(transport)
        assert req.method == "GET"
        assert "/event-types/evt_1" in str(req.url)

    def test_update_sends_patch_with_body(self, _patch_client):
        transport = _patch_client({"id": "evt_1"})
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.event_types.update("ws_abc", "evt_1", description="Updated")
        req = _last_request(transport)
        assert req.method == "PATCH"
        body = json.loads(req.content)
        assert body["description"] == "Updated"

    def test_delete_sends_delete(self, _patch_client):
        transport = _patch_client(None, 204)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.event_types.delete("ws_abc", "evt_1")
        req = _last_request(transport)
        assert req.method == "DELETE"


# ── Applications ──


class TestApplications:
    def test_list_sends_get_with_query_params(self, _patch_client):
        transport = _patch_client([{"id": "app_1", "name": "Acme"}])
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.applications.list("ws_abc", limit=10, offset=20)
        req = _last_request(transport)
        assert req.method == "GET"
        assert "/applications" in str(req.url)
        assert "limit=10" in str(req.url)
        assert "offset=20" in str(req.url)
        assert len(result["data"]) == 1

    def test_list_omits_undefined_query_params(self, _patch_client):
        transport = _patch_client([])
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.applications.list("ws_abc")
        req = _last_request(transport)
        assert str(req.url) == "https://api.test.com/management/v1/workspaces/ws_abc/applications"

    def test_create_sends_post_with_body(self, _patch_client):
        transport = _patch_client({"id": "app_new", "name": "Acme"}, 201)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.applications.create("ws_abc", name="Acme", external_id="ext-1")
        req = _last_request(transport)
        assert req.method == "POST"
        body = json.loads(req.content)
        assert body["name"] == "Acme"
        assert body["externalId"] == "ext-1"

    def test_get_sends_get_to_application_id(self, _patch_client):
        transport = _patch_client({"id": "app_1"})
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.applications.get("ws_abc", "app_1")
        req = _last_request(transport)
        assert req.method == "GET"
        assert "/applications/app_1" in str(req.url)

    def test_update_sends_patch(self, _patch_client):
        transport = _patch_client({"id": "app_1"})
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.applications.update("ws_abc", "app_1", name="Updated")
        req = _last_request(transport)
        assert req.method == "PATCH"
        body = json.loads(req.content)
        assert body["name"] == "Updated"

    def test_delete_sends_delete(self, _patch_client):
        transport = _patch_client(None, 204)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.applications.delete("ws_abc", "app_1")
        req = _last_request(transport)
        assert req.method == "DELETE"

    def test_list_endpoints_sends_get(self, _patch_client):
        transport = _patch_client([{"id": "ep_1"}])
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.applications.list_endpoints("ws_abc", "app_1")
        req = _last_request(transport)
        assert req.method == "GET"
        assert "/applications/app_1/endpoints" in str(req.url)
        assert len(result["data"]) == 1

    def test_create_endpoint_sends_post(self, _patch_client):
        transport = _patch_client({"id": "ep_new"}, 201)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.applications.create_endpoint("ws_abc", "app_1", url="https://example.com")
        req = _last_request(transport)
        assert req.method == "POST"
        assert "/applications/app_1/endpoints" in str(req.url)
        body = json.loads(req.content)
        assert body["url"] == "https://example.com"


# ── Subscriptions ──


class TestSubscriptions:
    def test_list_sends_get_to_subscriptions(self, _patch_client):
        transport = _patch_client([{"id": "sub_1"}])
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.subscriptions.list("ws_abc", "ep_1")
        req = _last_request(transport)
        assert req.method == "GET"
        assert str(req.url) == "https://api.test.com/management/v1/workspaces/ws_abc/endpoints/ep_1/subscriptions"
        assert len(result["data"]) == 1

    def test_create_sends_post_with_event_type_id(self, _patch_client):
        transport = _patch_client({"id": "sub_new"}, 201)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.subscriptions.create("ws_abc", "ep_1", event_type_id="evt_1")
        req = _last_request(transport)
        assert req.method == "POST"
        body = json.loads(req.content)
        assert body["eventTypeId"] == "evt_1"

    def test_delete_sends_delete_with_event_type_id_in_path(self, _patch_client):
        transport = _patch_client(None, 204)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.subscriptions.delete("ws_abc", "ep_1", "evt_1")
        req = _last_request(transport)
        assert req.method == "DELETE"
        assert "/subscriptions/evt_1" in str(req.url)


# ── Portal Sessions ──


class TestPortalSessions:
    def test_create_sends_post_with_metadata(self, _patch_client):
        transport = _patch_client(
            {"url": "https://portal.nahook.com/s/abc", "code": "xyz", "expiresAt": "2026-04-10T12:00:00Z"},
            201,
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.portal_sessions.create("ws_abc", "app_1", metadata={"userId": "u-1"})
        req = _last_request(transport)
        assert req.method == "POST"
        assert "/applications/app_1/portal" in str(req.url)
        body = json.loads(req.content)
        assert body["metadata"]["userId"] == "u-1"
        assert "portal.nahook.com" in result["url"]

    def test_create_sends_empty_body_when_no_options(self, _patch_client):
        transport = _patch_client(
            {"url": "https://portal.nahook.com/s/abc", "code": "xyz", "expiresAt": "2026-04-10T12:00:00Z"},
            201,
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.portal_sessions.create("ws_abc", "app_1")
        req = _last_request(transport)
        body = json.loads(req.content)
        assert body == {}


# ── Headers ──


class TestHeaders:
    def test_sends_authorization_header(self, _patch_client):
        transport = _patch_client([])
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.endpoints.list("ws_abc")
        req = _last_request(transport)
        assert req.headers["authorization"] == "Bearer nhm_test123"

    def test_sends_user_agent_header(self, _patch_client):
        transport = _patch_client([])
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.endpoints.list("ws_abc")
        req = _last_request(transport)
        assert req.headers["user-agent"].startswith("nahook-python/")

    def test_omits_content_type_on_get_requests(self, _patch_client):
        transport = _patch_client([])
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.endpoints.list("ws_abc")
        req = _last_request(transport)
        assert "content-type" not in req.headers

    def test_includes_content_type_on_post_requests(self, _patch_client):
        transport = _patch_client({"id": "ep_new"}, 201)
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.endpoints.create("ws_abc", url="https://example.com")
        req = _last_request(transport)
        assert req.headers["content-type"] == "application/json"


# ── Client methods ──


class TestNahookClient:
    def test_send_calls_correct_endpoint(self, _patch_client):
        transport = _patch_client(
            {"deliveryId": "del_abc", "idempotencyKey": "key-1", "status": "accepted"}, 202
        )
        client = NahookClient("nhk_us_test123", base_url=BASE_URL)
        result = client.send("ep_123", {"test": True})
        req = _last_request(transport)
        assert "/api/ingest/ep_123" in str(req.url)
        assert req.method == "POST"
        assert result["deliveryId"] == "del_abc"
        assert result["status"] == "accepted"

    def test_trigger_calls_correct_endpoint(self, _patch_client):
        transport = _patch_client(
            {"eventTypeId": "evt_abc", "deliveryIds": ["del_1"], "status": "accepted"}, 202
        )
        client = NahookClient("nhk_us_test123", base_url=BASE_URL)
        result = client.trigger("order.paid", {"orderId": "123"})
        req = _last_request(transport)
        assert "/api/ingest/event/order.paid" in str(req.url)
        assert result["eventTypeId"] == "evt_abc"

    def test_send_batch_calls_correct_endpoint(self, _patch_client):
        transport = _patch_client(
            {"items": [{"index": 0, "deliveryId": "del_abc", "status": "accepted"}]}, 202
        )
        client = NahookClient("nhk_us_test123", base_url=BASE_URL)
        result = client.send_batch([{"endpointId": "ep_123", "payload": {"test": True}}])
        req = _last_request(transport)
        assert "/api/ingest/batch" in str(req.url)
        assert len(result["items"]) == 1
        assert result["items"][0]["status"] == "accepted"

    def test_trigger_batch_calls_correct_endpoint(self, _patch_client):
        transport = _patch_client(
            {"items": [{"index": 0, "eventTypeId": "evt_abc", "deliveryIds": [], "status": "accepted"}]}, 202
        )
        client = NahookClient("nhk_us_test123", base_url=BASE_URL)
        result = client.trigger_batch([{"eventType": "order.paid", "payload": {"orderId": "123"}}])
        req = _last_request(transport)
        assert "/api/ingest/event/batch" in str(req.url)
        assert len(result["items"]) == 1

    def test_throws_nahook_api_error_on_error_response(self, _patch_client):
        _patch_client({"error": {"code": "not_found", "message": "Endpoint not found"}}, 404)
        client = NahookClient("nhk_us_test123", base_url=BASE_URL)
        with pytest.raises(NahookAPIError, match="Endpoint not found"):
            client.send("ep_missing", {})
