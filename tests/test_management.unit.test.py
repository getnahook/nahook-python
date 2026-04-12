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
