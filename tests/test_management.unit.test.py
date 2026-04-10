"""Unit tests for NahookManagement.

Uses unittest.mock to patch httpx.Client and capture calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nahook import NahookManagement
from nahook.resources.applications import ApplicationsResource
from nahook.resources.endpoints import EndpointsResource
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
