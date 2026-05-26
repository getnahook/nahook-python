"""
Nahook Python SDK — Integration Tests

Prerequisites:
  1. Local API running (e.g. via integration test orchestration script)
  2. Environment variables set:
     - NAHOOK_TEST_API_URL        (e.g. http://localhost:3099)
     - NAHOOK_TEST_API_KEY        (e.g. nhk_us_testfixture_aaaa1111bbbb2222)
     - NAHOOK_TEST_DISABLED_API_KEY
     - NAHOOK_TEST_ENDPOINT_ID    (e.g. ep_integration_test_001)
     - NAHOOK_TEST_EVENT_TYPE     (e.g. order.created)

  These tests hit a real API and are NOT meant for CI unit-test runs.
  Run with:  pytest -c pytest.integration.ini
"""

import os
import uuid

import pytest

from nahook import NahookClient, NahookAPIError

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

API_URL = os.environ.get("NAHOOK_TEST_API_URL")
API_KEY = os.environ.get("NAHOOK_TEST_API_KEY")
DISABLED_API_KEY = os.environ.get("NAHOOK_TEST_DISABLED_API_KEY")
ENDPOINT_ID = os.environ.get("NAHOOK_TEST_ENDPOINT_ID")
EVENT_TYPE = os.environ.get("NAHOOK_TEST_EVENT_TYPE")

REQUIRED_VARS = {
    "NAHOOK_TEST_API_URL": API_URL,
    "NAHOOK_TEST_API_KEY": API_KEY,
    "NAHOOK_TEST_DISABLED_API_KEY": DISABLED_API_KEY,
    "NAHOOK_TEST_ENDPOINT_ID": ENDPOINT_ID,
    "NAHOOK_TEST_EVENT_TYPE": EVENT_TYPE,
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
def client() -> NahookClient:
    return NahookClient(API_KEY, base_url=API_URL)


@pytest.fixture()
def disabled_client() -> NahookClient:
    return NahookClient(DISABLED_API_KEY, base_url=API_URL)


def _make_payload() -> dict:
    return {"orderId": str(uuid.uuid4()), "amount": 49.99}


# ---------------------------------------------------------------------------
# send() tests
# ---------------------------------------------------------------------------


def test_send_happy_path(client: NahookClient):
    """send() to a valid endpoint returns accepted with a delivery ID."""
    result = client.send(ENDPOINT_ID, payload=_make_payload())

    assert result["status"] == "accepted"
    assert result["deliveryId"].startswith("del_")
    assert "idempotencyKey" in result


def test_send_idempotency_dedup(client: NahookClient):
    """Sending twice with the same idempotencyKey returns the same deliveryId."""
    key = str(uuid.uuid4())
    r1 = client.send(ENDPOINT_ID, payload=_make_payload(), idempotency_key=key)
    r2 = client.send(ENDPOINT_ID, payload=_make_payload(), idempotency_key=key)

    assert r1["deliveryId"] == r2["deliveryId"]


def test_send_separate_keys(client: NahookClient):
    """Different idempotencyKeys produce different deliveryIds."""
    r1 = client.send(ENDPOINT_ID, payload=_make_payload(), idempotency_key=str(uuid.uuid4()))
    r2 = client.send(ENDPOINT_ID, payload=_make_payload(), idempotency_key=str(uuid.uuid4()))

    assert r1["deliveryId"] != r2["deliveryId"]


# ---------------------------------------------------------------------------
# trigger() tests
# ---------------------------------------------------------------------------


def test_trigger_fan_out(client: NahookClient):
    """trigger() a subscribed event type fans out to at least one delivery."""
    result = client.trigger(EVENT_TYPE, payload=_make_payload())

    assert result["status"] == "accepted"
    assert result["eventTypeId"].startswith("evt_")
    assert len(result["deliveryIds"]) >= 1
    for did in result["deliveryIds"]:
        assert did.startswith("del_")


def test_trigger_unsubscribed(client: NahookClient):
    """trigger() an event type with no subscribers returns empty deliveryIds."""
    # Pre-seeded fixture event type with zero subscriptions — shared across all SDK
    # integration tests. See packages/db/src/seeds/test-fixtures.sql section 8b.
    result = client.trigger("event.type.nobody.subscribed.to", payload=_make_payload())

    assert result["deliveryIds"] == [] or len(result["deliveryIds"]) == 0


# ---------------------------------------------------------------------------
# sendBatch() tests
# ---------------------------------------------------------------------------


def test_send_batch(client: NahookClient):
    """sendBatch() with 2 items returns 2 accepted deliveries."""
    items = [
        {"endpointId": ENDPOINT_ID, "payload": _make_payload()},
        {"endpointId": ENDPOINT_ID, "payload": _make_payload()},
    ]
    result = client.send_batch(items)

    assert len(result["items"]) == 2
    for item in result["items"]:
        assert item["status"] == "accepted"
        assert item["deliveryId"].startswith("del_")


# ---------------------------------------------------------------------------
# triggerBatch() tests
# ---------------------------------------------------------------------------


def test_trigger_batch(client: NahookClient):
    """triggerBatch() with 2 items returns 2 accepted triggers."""
    items = [
        {"eventType": EVENT_TYPE, "payload": _make_payload()},
        {"eventType": EVENT_TYPE, "payload": _make_payload()},
    ]
    result = client.trigger_batch(items)

    assert len(result["items"]) == 2
    for item in result["items"]:
        assert item["status"] == "accepted"
        assert item["eventTypeId"].startswith("evt_")


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_401_invalid_key():
    """A garbage API key returns 401 with is_auth_error."""
    bad_client = NahookClient("nhk_us_garbage_totallyinvalid", base_url=API_URL)

    with pytest.raises(NahookAPIError) as exc_info:
        bad_client.send(ENDPOINT_ID, payload=_make_payload())

    err = exc_info.value
    assert err.status == 401
    assert err.is_auth_error is True
    assert err.is_retryable is False


def test_403_disabled_key(disabled_client: NahookClient):
    """A disabled API key returns 403 with code token_disabled."""
    with pytest.raises(NahookAPIError) as exc_info:
        disabled_client.send(ENDPOINT_ID, payload=_make_payload())

    err = exc_info.value
    assert err.status == 403
    assert err.code == "token_disabled"
    assert err.is_auth_error is True


def test_404_missing_endpoint(client: NahookClient):
    """Sending to a non-existent endpoint returns 404."""
    with pytest.raises(NahookAPIError) as exc_info:
        client.send("ep_nonexistent_endpoint_id_000", payload=_make_payload())

    err = exc_info.value
    assert err.status == 404
    assert err.is_not_found is True


def test_400_invalid_event_type(client: NahookClient):
    """Triggering with an invalid event type name returns 400."""
    with pytest.raises(NahookAPIError) as exc_info:
        client.trigger("INVALID NAME!!", payload=_make_payload())

    err = exc_info.value
    assert err.status == 400
    assert err.is_validation_error is True
