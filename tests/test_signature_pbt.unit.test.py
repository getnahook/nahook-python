"""Property-based tests for webhook signature operations using Hypothesis.

Validates that sign/verify invariants hold for arbitrary inputs.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

from hypothesis import given, settings
from hypothesis import strategies as st


# ── Signature helpers (same logic as SDK / test_webhook_signature) ──


def _compute_signature(secret_b64: str, msg_id: str, timestamp: str, payload: str) -> str:
    """Compute a v1 HMAC-SHA256 signature from a base64-encoded secret."""
    key = base64.b64decode(secret_b64)
    to_sign = f"{msg_id}.{timestamp}.{payload}".encode()
    digest = hmac.new(key, to_sign, hashlib.sha256).digest()
    return f"v1,{base64.b64encode(digest).decode()}"


def _verify_signature(
    secret_b64: str, msg_id: str, timestamp: str, payload: str, signature: str
) -> bool:
    expected = _compute_signature(secret_b64, msg_id, timestamp, payload)
    return hmac.compare_digest(expected, signature)


# Strategy: generate a valid base64-encoded secret (16-64 random bytes)
_secret_strategy = st.binary(min_size=16, max_size=64).map(
    lambda b: base64.b64encode(b).decode()
)
_msg_id_strategy = st.text(min_size=1, max_size=100)
_timestamp_strategy = st.integers(min_value=1000000000, max_value=9999999999).map(str)
_payload_strategy = st.text(min_size=0, max_size=5000)


class TestSignThenVerify:
    """Property 1: sign then verify always succeeds."""

    @given(
        secret=_secret_strategy,
        msg_id=_msg_id_strategy,
        timestamp=_timestamp_strategy,
        payload=_payload_strategy,
    )
    @settings(max_examples=100)
    def test_sign_then_verify_roundtrip(self, secret, msg_id, timestamp, payload):
        sig = _compute_signature(secret, msg_id, timestamp, payload)
        assert _verify_signature(secret, msg_id, timestamp, payload, sig)


class TestTamperedPayloadFails:
    """Property 2: tampered payload always fails verification."""

    @given(
        secret=_secret_strategy,
        msg_id=_msg_id_strategy,
        timestamp=_timestamp_strategy,
        payload=_payload_strategy,
        tampered=_payload_strategy,
    )
    @settings(max_examples=100)
    def test_tampered_payload_fails(self, secret, msg_id, timestamp, payload, tampered):
        # Only test when payloads actually differ
        if payload == tampered:
            return
        sig = _compute_signature(secret, msg_id, timestamp, payload)
        assert not _verify_signature(secret, msg_id, timestamp, tampered, sig)


class TestWrongSecretFails:
    """Property 3: wrong secret always fails verification."""

    @given(
        secret1=_secret_strategy,
        secret2=_secret_strategy,
        msg_id=_msg_id_strategy,
        timestamp=_timestamp_strategy,
        payload=_payload_strategy,
    )
    @settings(max_examples=100)
    def test_wrong_secret_fails(self, secret1, secret2, msg_id, timestamp, payload):
        # Only test when secrets actually differ
        if secret1 == secret2:
            return
        sig = _compute_signature(secret1, msg_id, timestamp, payload)
        assert not _verify_signature(secret2, msg_id, timestamp, payload, sig)


class TestSignDeterministic:
    """Property 4: sign is deterministic - same inputs produce same output."""

    @given(
        secret=_secret_strategy,
        msg_id=_msg_id_strategy,
        timestamp=_timestamp_strategy,
        payload=_payload_strategy,
    )
    @settings(max_examples=100)
    def test_sign_is_deterministic(self, secret, msg_id, timestamp, payload):
        sig1 = _compute_signature(secret, msg_id, timestamp, payload)
        sig2 = _compute_signature(secret, msg_id, timestamp, payload)
        assert sig1 == sig2
