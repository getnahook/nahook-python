"""Unit tests for NahookManagement.

Uses unittest.mock to patch httpx.Client and capture calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nahook import NahookManagement
import httpx
import json

from nahook.resources.applications import ApplicationsResource
from nahook.resources.deliveries import DeliveriesResource
from nahook.resources.endpoints import EndpointsResource
from nahook.resources.environments import EnvironmentsResource
from nahook.resources.event_types import EventTypesResource
from nahook.resources.portal_sessions import PortalSessionsResource
from nahook.resources.subscriptions import SubscriptionsResource


TOKEN = "nhm_test123"
BASE_URL = "https://api.test.com"


@pytest.fixture()
def mock_httpx_client():
    """Patch httpx.Client so no real HTTP calls are made."""
    with patch("nahook.http_client.httpx.Client") as MockClient:
        mock = MockClient.return_value
        mock.close = MagicMock()
        yield mock


# ── Token validation ──


class TestTokenValidation:
    def test_management_rejects_invalid_token(self):
        with pytest.raises(ValueError, match="must start with 'nhm_'"):
            NahookManagement("bad_token")

    def test_management_rejects_nhk_prefix(self):
        with pytest.raises(ValueError, match="must start with 'nhm_'"):
            NahookManagement("nhk_api_key")

    def test_management_accepts_valid_token(self, mock_httpx_client):
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        assert mgmt is not None


# ── Resource availability ──


class TestResources:
    def test_management_has_all_resources(self, mock_httpx_client):
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)

        assert hasattr(mgmt, "endpoints")
        assert isinstance(mgmt.endpoints, EndpointsResource)

        assert hasattr(mgmt, "event_types")
        assert isinstance(mgmt.event_types, EventTypesResource)

        assert hasattr(mgmt, "applications")
        assert isinstance(mgmt.applications, ApplicationsResource)

        assert hasattr(mgmt, "subscriptions")
        assert isinstance(mgmt.subscriptions, SubscriptionsResource)

        assert hasattr(mgmt, "portal_sessions")
        assert isinstance(mgmt.portal_sessions, PortalSessionsResource)

        assert hasattr(mgmt, "environments")
        assert isinstance(mgmt.environments, EnvironmentsResource)

        assert hasattr(mgmt, "deliveries")
        assert isinstance(mgmt.deliveries, DeliveriesResource)


# ── Context manager ──


class TestLifecycle:
    def test_management_is_context_manager(self, mock_httpx_client):
        with NahookManagement(TOKEN, base_url=BASE_URL) as mgmt:
            assert mgmt is not None
        mock_httpx_client.close.assert_called_once()

    def test_close_calls_httpx_close(self, mock_httpx_client):
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.close()
        mock_httpx_client.close.assert_called_once()


# ── Environments resource methods ──


class TestEnvironmentsResource:
    def test_list(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps([{"id": "env_1", "name": "Production", "slug": "production", "isDefault": True}]).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.environments.list("ws_abc")
        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == "env_1"
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "GET"
        assert "/workspaces/ws_abc/environments" in call_args.kwargs["url"]

    def test_create(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            201, content=json.dumps({"id": "env_new", "name": "Staging", "slug": "staging", "isDefault": False}).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.environments.create("ws_abc", name="Staging", slug="staging")
        assert result["id"] == "env_new"
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "POST"
        assert "/workspaces/ws_abc/environments" in call_args.kwargs["url"]

    def test_get(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps({"id": "env_1", "name": "Production"}).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.environments.get("ws_abc", "env_1")
        assert result["id"] == "env_1"
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "GET"
        assert "/environments/env_1" in call_args.kwargs["url"]

    def test_update(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps({"id": "env_1", "name": "Pre-production"}).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.environments.update("ws_abc", "env_1", name="Pre-production")
        assert result["name"] == "Pre-production"
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "PATCH"
        assert "/environments/env_1" in call_args.kwargs["url"]

    def test_delete(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(204, content=b"")
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.environments.delete("ws_abc", "env_1")
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "DELETE"
        assert "/environments/env_1" in call_args.kwargs["url"]

    def test_list_event_type_visibility(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps([{"eventTypeName": "order.created", "published": True}]).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.environments.list_event_type_visibility("ws_abc", "env_1")
        assert len(result["data"]) == 1
        assert result["data"][0]["published"] is True
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "GET"
        assert "/environments/env_1/event-types" in call_args.kwargs["url"]

    def test_set_event_type_visibility(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps({"eventTypeName": "order.created", "published": True}).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.environments.set_event_type_visibility("ws_abc", "env_1", "evt_1", published=True)
        assert result["published"] is True
        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "PUT"
        assert "/environments/env_1/event-types/evt_1/visibility" in call_args.kwargs["url"]


# ── Deliveries resource methods ──


class TestDeliveriesResource:
    """Unit tests for the deliveries resource — wire shape and URL/query assertions."""

    _DEL_A = {
        "id": "del_a",
        "idempotencyKey": "k1",
        "endpointId": "ep_1",
        "status": "delivered",
        "totalAttempts": 1,
        "firstAttemptAt": "2026-05-28T14:30:59Z",
        "deliveredAt": "2026-05-28T14:30:59Z",
        "nextRetryAt": None,
        "hasPayload": True,
        "createdAt": "2026-05-28T14:30:59Z",
        "updatedAt": "2026-05-28T14:30:59Z",
    }

    _DEL_B = {
        "id": "del_b",
        "idempotencyKey": "k2",
        "endpointId": "ep_1",
        "status": "failed",
        "totalAttempts": 3,
        "firstAttemptAt": "2026-05-28T14:31:00Z",
        "deliveredAt": None,
        "nextRetryAt": None,
        "hasPayload": False,
        "createdAt": "2026-05-28T14:31:00Z",
        "updatedAt": "2026-05-28T14:31:00Z",
    }

    def test_list_returns_paginated_data_and_next_cursor(self, mock_httpx_client):
        body = {"deliveries": [self._DEL_A, self._DEL_B], "nextCursor": "opaque-token-aaa"}
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps(body).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.deliveries.list("ws_abc", "ep_1")

        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "GET"
        assert (
            call_args.kwargs["url"]
            == "https://api.test.com/management/v1/workspaces/ws_abc/endpoints/ep_1/deliveries"
        )
        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "del_a"
        assert result["next_cursor"] == "opaque-token-aaa"

    def test_list_returns_null_cursor_when_last_page(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps({"deliveries": [], "nextCursor": None}).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        result = mgmt.deliveries.list("ws_abc", "ep_1")

        assert result["data"] == []
        assert result["next_cursor"] is None

    def test_list_forwards_query_params(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps({"deliveries": [], "nextCursor": None}).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.deliveries.list(
            "ws_abc", "ep_1", limit=25, cursor="opaque-token-xyz", status="failed"
        )

        url = mock_httpx_client.request.call_args.kwargs["url"]
        assert "limit=25" in url
        assert "cursor=opaque-token-xyz" in url
        assert "status=failed" in url

    def test_list_omits_unset_query_params(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps({"deliveries": [], "nextCursor": None}).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        mgmt.deliveries.list("ws_abc", "ep_1")

        url = mock_httpx_client.request.call_args.kwargs["url"]
        # No query string at all when no options are passed.
        assert "?" not in url
        assert "limit=" not in url
        assert "cursor=" not in url
        assert "status=" not in url

    def test_get_returns_metadata_without_envelope_by_default(self, mock_httpx_client):
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps(self._DEL_A).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        delivery = mgmt.deliveries.get("ws_abc", "del_a")

        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "GET"
        assert (
            call_args.kwargs["url"]
            == "https://api.test.com/management/v1/workspaces/ws_abc/deliveries/del_a"
        )
        # No include=payload query when the flag is unset.
        assert "include=" not in call_args.kwargs["url"]
        assert delivery["id"] == "del_a"
        assert delivery["hasPayload"] is True
        assert "payload" not in delivery

    def test_get_with_include_payload_returns_envelope(self, mock_httpx_client):
        body = {
            **self._DEL_A,
            "payload": {
                "status": "available",
                "data": {"orderId": "ord_123"},
                "contentType": "application/json",
            },
        }
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps(body).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        delivery = mgmt.deliveries.get("ws_abc", "del_a", include_payload=True)

        url = mock_httpx_client.request.call_args.kwargs["url"]
        assert "include=payload" in url
        assert delivery["payload"] == {
            "status": "available",
            "data": {"orderId": "ord_123"},
            "contentType": "application/json",
        }

    def test_get_returns_forbidden_envelope_for_plan_gated_workspace(self, mock_httpx_client):
        body = {**self._DEL_A, "payload": {"status": "forbidden"}}
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps(body).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        delivery = mgmt.deliveries.get("ws_abc", "del_a", include_payload=True)

        # forbidden is surfaced unchanged — the HTTP layer does NOT raise.
        assert delivery["payload"] == {"status": "forbidden"}

    def test_get_attempts_returns_array(self, mock_httpx_client):
        attempts_body = [
            {
                "id": "att_1",
                "attemptNumber": 1,
                "status": "failed",
                "responseStatusCode": 502,
                "responseTimeMs": 142,
                "errorMessage": "Bad gateway",
                "createdAt": "2026-05-28T14:31:00Z",
            },
            {
                "id": "att_2",
                "attemptNumber": 2,
                "status": "success",
                "responseStatusCode": 200,
                "responseTimeMs": 88,
                "errorMessage": None,
                "createdAt": "2026-05-28T14:31:30Z",
            },
        ]
        mock_httpx_client.request.return_value = httpx.Response(
            200, content=json.dumps(attempts_body).encode()
        )
        mgmt = NahookManagement(TOKEN, base_url=BASE_URL)
        attempts = mgmt.deliveries.get_attempts("ws_abc", "del_a")

        call_args = mock_httpx_client.request.call_args
        assert call_args.kwargs["method"] == "GET"
        assert (
            call_args.kwargs["url"]
            == "https://api.test.com/management/v1/workspaces/ws_abc/deliveries/del_a/attempts"
        )
        assert len(attempts) == 2
        assert attempts[0]["attemptNumber"] == 1
        assert attempts[1]["status"] == "success"
