"""
Nahook Python SDK — Management API Integration Tests

Prerequisites:
  1. Local API running (e.g. via integration test orchestration script)
  2. Environment variables set:
     - NAHOOK_TEST_API_URL        (e.g. http://localhost:3099)
     - NAHOOK_TEST_MGMT_TOKEN     (e.g. nhm_...)
     - NAHOOK_TEST_WORKSPACE_ID   (e.g. ws_...)

  These tests hit a real API and are NOT meant for CI unit-test runs.
"""

import os
import time

import pytest

from nahook.management import NahookManagement
from nahook.errors import NahookAPIError

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

API_URL = os.environ.get("NAHOOK_TEST_API_URL")
MGMT_TOKEN = os.environ.get("NAHOOK_TEST_MGMT_TOKEN")
WORKSPACE_ID = os.environ.get("NAHOOK_TEST_WORKSPACE_ID")

REQUIRED_VARS = {
    "NAHOOK_TEST_API_URL": API_URL,
    "NAHOOK_TEST_MGMT_TOKEN": MGMT_TOKEN,
    "NAHOOK_TEST_WORKSPACE_ID": WORKSPACE_ID,
}

_missing = [k for k, v in REQUIRED_VARS.items() if not v]
if _missing:
    pytest.skip(
        f"Missing required env vars: {', '.join(_missing)}",
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mgmt() -> NahookManagement:
    return NahookManagement(MGMT_TOKEN, base_url=API_URL)


def _ts() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# Event Types CRUD
# ---------------------------------------------------------------------------


class TestEventTypes:
    def test_crud_lifecycle(self, mgmt: NahookManagement):
        """Create, list, get, update, delete an event type."""
        ts = _ts()
        name = f"mgmt.test.{ts}"

        # Create
        created = mgmt.event_types.create(
            WORKSPACE_ID,
            name=name,
            description="Integration test event type",
        )
        event_type_id = created["id"]
        assert created["name"] == name
        assert created["description"] == "Integration test event type"

        # List — should contain at least our new event type
        listed = mgmt.event_types.list(WORKSPACE_ID)
        assert len(listed["data"]) >= 1

        # Get by id
        fetched = mgmt.event_types.get(WORKSPACE_ID, event_type_id)
        assert fetched["id"] == event_type_id
        assert fetched["name"] == name

        # Update description
        updated = mgmt.event_types.update(
            WORKSPACE_ID,
            event_type_id,
            description="Updated description",
        )
        assert updated["description"] == "Updated description"

        # Delete
        mgmt.event_types.delete(WORKSPACE_ID, event_type_id)

        # Verify 404
        with pytest.raises(NahookAPIError) as exc_info:
            mgmt.event_types.get(WORKSPACE_ID, event_type_id)
        assert exc_info.value.status == 404


# ---------------------------------------------------------------------------
# Endpoints CRUD
# ---------------------------------------------------------------------------


class TestEndpoints:
    def test_crud_lifecycle(self, mgmt: NahookManagement):
        """Create, list, get, update, delete an endpoint."""
        ts = _ts()

        # Create
        created = mgmt.endpoints.create(
            WORKSPACE_ID,
            url="https://httpbin.org/post",
            description=f"Integration test endpoint {ts}",
        )
        endpoint_id = created["id"]
        assert "https://httpbin.org/post" in created["url"]
        assert created["description"] == f"Integration test endpoint {ts}"

        # List
        listed = mgmt.endpoints.list(WORKSPACE_ID)
        assert len(listed["data"]) >= 1

        # Get by id
        fetched = mgmt.endpoints.get(WORKSPACE_ID, endpoint_id)
        assert fetched["id"] == endpoint_id

        # Update description and deactivate
        updated = mgmt.endpoints.update(
            WORKSPACE_ID,
            endpoint_id,
            description="Updated endpoint",
            is_active=False,
        )
        assert updated["description"] == "Updated endpoint"
        assert updated["isActive"] is False

        # Delete
        mgmt.endpoints.delete(WORKSPACE_ID, endpoint_id)

        # Verify 404
        with pytest.raises(NahookAPIError) as exc_info:
            mgmt.endpoints.get(WORKSPACE_ID, endpoint_id)
        assert exc_info.value.status == 404


# ---------------------------------------------------------------------------
# Applications CRUD
# ---------------------------------------------------------------------------


class TestApplications:
    def test_crud_lifecycle(self, mgmt: NahookManagement):
        """Create, list, get, update, delete an application."""
        ts = _ts()

        # Create
        created = mgmt.applications.create(
            WORKSPACE_ID,
            name=f"Test App {ts}",
            metadata={"env": "test"},
        )
        app_id = created["id"]
        assert created["name"] == f"Test App {ts}"

        # List
        listed = mgmt.applications.list(WORKSPACE_ID)
        assert len(listed["data"]) >= 1

        # Get by id
        fetched = mgmt.applications.get(WORKSPACE_ID, app_id)
        assert fetched["id"] == app_id

        # Update name
        updated = mgmt.applications.update(
            WORKSPACE_ID,
            app_id,
            name=f"Renamed App {ts}",
        )
        assert updated["name"] == f"Renamed App {ts}"

        # Delete
        mgmt.applications.delete(WORKSPACE_ID, app_id)

        # Verify 404
        with pytest.raises(NahookAPIError) as exc_info:
            mgmt.applications.get(WORKSPACE_ID, app_id)
        assert exc_info.value.status == 404


# ---------------------------------------------------------------------------
# Subscriptions CRUD
# ---------------------------------------------------------------------------


class TestSubscriptions:
    def test_subscribe_unsubscribe_lifecycle(self, mgmt: NahookManagement):
        """Create endpoint + event type, subscribe, list, unsubscribe, verify gone."""
        ts = _ts()

        # Create prerequisite event type
        event_type = mgmt.event_types.create(
            WORKSPACE_ID,
            name=f"sub.test.{ts}",
            description="For subscription test",
        )
        event_type_id = event_type["id"]

        # Create prerequisite endpoint
        endpoint = mgmt.endpoints.create(
            WORKSPACE_ID,
            url="https://httpbin.org/post",
            description=f"Sub test endpoint {ts}",
        )
        endpoint_id = endpoint["id"]

        try:
            # Subscribe — API expects eventTypeIds (plural array), returns {subscribed: N}
            result = mgmt.subscriptions.create(
                WORKSPACE_ID,
                endpoint_id,
                event_type_ids=[event_type_id],
            )
            assert result["subscribed"] == 1

            # List — find our subscription
            listed = mgmt.subscriptions.list(WORKSPACE_ID, endpoint_id)
            assert len(listed["data"]) >= 1
            matching = [
                s for s in listed["data"] if s.get("eventTypeId") == event_type_id
            ]
            assert len(matching) == 1

            # Unsubscribe — uses event type public_id in path, returns 204
            mgmt.subscriptions.delete(WORKSPACE_ID, endpoint_id, event_type_id)

            # Verify subscription is gone
            listed_after = mgmt.subscriptions.list(WORKSPACE_ID, endpoint_id)
            remaining_evt_ids = [
                s.get("eventTypeId") for s in listed_after["data"]
            ]
            assert event_type_id not in remaining_evt_ids
        finally:
            # Cleanup: delete endpoint and event type
            try:
                mgmt.endpoints.delete(WORKSPACE_ID, endpoint_id)
            except NahookAPIError:
                pass
            try:
                mgmt.event_types.delete(WORKSPACE_ID, event_type_id)
            except NahookAPIError:
                pass


# ---------------------------------------------------------------------------
# Auth error
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Environments CRUD
# ---------------------------------------------------------------------------


class TestEnvironments:
    def test_crud_lifecycle(self, mgmt: NahookManagement):
        """Create, list, get, update, delete an environment."""
        ts = _ts()

        # Create
        created = mgmt.environments.create(
            WORKSPACE_ID,
            name=f"Test Env {ts}",
            slug=f"test-env-{ts}",
        )
        env_id = created["id"]
        assert created["name"] == f"Test Env {ts}"
        assert created["slug"] == f"test-env-{ts}"
        assert created["isDefault"] is False

        # List — should contain at least 2 (default + ours)
        listed = mgmt.environments.list(WORKSPACE_ID)
        assert len(listed["data"]) >= 2

        # Get by id
        fetched = mgmt.environments.get(WORKSPACE_ID, env_id)
        assert fetched["id"] == env_id
        assert fetched["name"] == f"Test Env {ts}"

        # Update name
        updated = mgmt.environments.update(
            WORKSPACE_ID,
            env_id,
            name=f"Renamed Env {ts}",
        )
        assert updated["name"] == f"Renamed Env {ts}"

        # Delete
        mgmt.environments.delete(WORKSPACE_ID, env_id)

        # Verify 404
        with pytest.raises(NahookAPIError) as exc_info:
            mgmt.environments.get(WORKSPACE_ID, env_id)
        assert exc_info.value.status == 404


# ---------------------------------------------------------------------------
# Event Type Visibility
# ---------------------------------------------------------------------------


class TestEventTypeVisibility:
    def test_visibility_lifecycle(self, mgmt: NahookManagement):
        """Create env + event type, toggle visibility, verify."""
        ts = _ts()

        # Create prerequisite environment
        env = mgmt.environments.create(
            WORKSPACE_ID,
            name=f"Vis Env {ts}",
            slug=f"vis-env-{ts}",
        )
        env_id = env["id"]

        # Create prerequisite event type
        event_type = mgmt.event_types.create(
            WORKSPACE_ID,
            name=f"vis.test.{ts}",
            description="For visibility test",
        )
        event_type_id = event_type["id"]

        try:
            # List visibility — all unpublished by default
            listed = mgmt.environments.list_event_type_visibility(
                WORKSPACE_ID, env_id
            )
            assert isinstance(listed["data"], list)
            matching = [
                v for v in listed["data"] if v["eventTypeId"] == event_type_id
            ]
            if matching:
                assert matching[0]["published"] is False

            # Set published = True
            result = mgmt.environments.set_event_type_visibility(
                WORKSPACE_ID,
                env_id,
                event_type_id,
                published=True,
            )
            assert result["eventTypeId"] == event_type_id
            assert result["published"] is True

            # Verify via list
            listed2 = mgmt.environments.list_event_type_visibility(
                WORKSPACE_ID, env_id
            )
            matching2 = [
                v for v in listed2["data"] if v["eventTypeId"] == event_type_id
            ]
            assert len(matching2) == 1
            assert matching2[0]["published"] is True

            # Set published = False
            result2 = mgmt.environments.set_event_type_visibility(
                WORKSPACE_ID,
                env_id,
                event_type_id,
                published=False,
            )
            assert result2["published"] is False

            # Verify via list
            listed3 = mgmt.environments.list_event_type_visibility(
                WORKSPACE_ID, env_id
            )
            matching3 = [
                v for v in listed3["data"] if v["eventTypeId"] == event_type_id
            ]
            assert len(matching3) == 1
            assert matching3[0]["published"] is False
        finally:
            # Cleanup
            try:
                mgmt.environments.delete(WORKSPACE_ID, env_id)
            except NahookAPIError:
                pass
            try:
                mgmt.event_types.delete(WORKSPACE_ID, event_type_id)
            except NahookAPIError:
                pass


# ---------------------------------------------------------------------------
# Auth error
# ---------------------------------------------------------------------------


class TestAuthError:
    def test_invalid_management_token(self):
        """An invalid management token raises NahookAPIError on any call."""
        bad_mgmt = NahookManagement("nhm_invalid_token", base_url=API_URL)

        with pytest.raises(NahookAPIError) as exc_info:
            bad_mgmt.event_types.list(WORKSPACE_ID)

        err = exc_info.value
        assert err.status in (401, 403)
        assert err.is_auth_error is True
