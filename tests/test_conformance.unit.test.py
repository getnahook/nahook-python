"""Conformance tests driven by shared JSON fixtures.

Loads fixtures from ../fixtures/conformance/ and validates that the Python SDK
behaves identically to all other SDKs for error classification, region routing,
retry backoff, and signature operations.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path

import pytest

from nahook.errors import NahookAPIError
from nahook.http_client import (
    BASE_DELAY_MS,
    MAX_DELAY_MS,
    _calculate_delay,
    _resolve_base_url,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "conformance"


def _load_fixtures(category: str):
    filepath = FIXTURES_DIR / category / "cases.json"
    with open(filepath, "r") as f:
        return json.load(f)


# ── Helpers: signature functions (same as in test_webhook_signature) ──


def _compute_signature(secret: str, msg_id: str, timestamp: str, payload: str) -> str:
    raw_secret = secret[6:] if secret.startswith("whsec_") else secret
    key = base64.b64decode(raw_secret)
    to_sign = f"{msg_id}.{timestamp}.{payload}".encode()
    digest = hmac.new(key, to_sign, hashlib.sha256).digest()
    return f"v1,{base64.b64encode(digest).decode()}"


def _verify_signature(
    secret: str, msg_id: str, timestamp: str, payload: str, signature: str
) -> bool:
    expected = _compute_signature(secret, msg_id, timestamp, payload)
    return hmac.compare_digest(expected, signature)


# ── Error classification ──


class TestErrorClassificationConformance:
    _cases = _load_fixtures("error-classification")

    @pytest.mark.parametrize(
        "case", _cases, ids=[c["id"] for c in _cases]
    )
    def test_error_flags(self, case):
        inp = case["input"]
        expect = case["expect"]
        retry_after = inp.get("retryAfter")
        error = NahookAPIError(
            inp["status"], inp["code"], inp["message"], retry_after=retry_after
        )
        assert error.is_retryable == expect["isRetryable"], f"{case['id']}: isRetryable"
        assert error.is_auth_error == expect["isAuthError"], f"{case['id']}: isAuthError"
        assert error.is_not_found == expect["isNotFound"], f"{case['id']}: isNotFound"
        assert error.is_rate_limited == expect["isRateLimited"], f"{case['id']}: isRateLimited"
        assert error.is_validation_error == expect["isValidationError"], f"{case['id']}: isValidationError"


# ── Region routing ──


class TestRegionRoutingConformance:
    _cases = _load_fixtures("region-routing")

    @pytest.mark.parametrize(
        "case", _cases, ids=[c["id"] for c in _cases]
    )
    def test_resolve_base_url(self, case):
        token = case["input"]["token"]
        expected_url = case["expect"]["baseUrl"]
        assert _resolve_base_url(token) == expected_url, case["id"]


# ── Retry backoff ──


class TestRetryBackoffConformance:
    _cases = _load_fixtures("retry-backoff")

    @pytest.mark.parametrize(
        "case", _cases, ids=[c["id"] for c in _cases]
    )
    def test_delay_bounds(self, case):
        inp = case["input"]
        expect = case["expect"]
        attempt = inp["attempt"]
        retry_after_ms = inp.get("retryAfterMs")

        if "exactDelayMs" in expect:
            delay = _calculate_delay(attempt, retry_after_ms=retry_after_ms)
            assert delay == expect["exactDelayMs"], case["id"]
        else:
            # Run multiple times because of jitter
            for _ in range(50):
                delay = _calculate_delay(attempt, retry_after_ms=retry_after_ms)
                assert expect["minDelayMs"] <= delay <= expect["maxDelayMs"], (
                    f"{case['id']}: delay {delay} not in [{expect['minDelayMs']}, {expect['maxDelayMs']}]"
                )


# ── Signature ──


class TestSignatureConformance:
    _cases = _load_fixtures("signature")

    @pytest.mark.parametrize(
        "case", _cases, ids=[c["id"] for c in _cases]
    )
    def test_signature_action(self, case):
        inp = case["input"]
        action = case["action"]
        expect = case["expect"]

        secret = inp["secret"]
        msg_id = inp["messageId"]
        timestamp = inp["timestamp"]

        # Handle payload generators
        if "payloadGenerator" in inp:
            gen = inp["payloadGenerator"]
            if gen == "repeat_a_10000":
                payload = "a" * 10000
            else:
                pytest.skip(f"Unknown payload generator: {gen}")
        else:
            payload = inp["payload"]

        if action == "sign_then_verify":
            sig = _compute_signature(secret, msg_id, timestamp, payload)
            result = _verify_signature(secret, msg_id, timestamp, payload, sig)
            assert result == expect["verifies"], case["id"]

        elif action == "sign_original_verify_tampered":
            sig = _compute_signature(secret, msg_id, timestamp, payload)
            tampered = inp["tamperedPayload"]
            result = _verify_signature(secret, msg_id, timestamp, tampered, sig)
            assert result == expect["verifies"], case["id"]

        elif action == "sign_with_original_verify_with_wrong":
            sig = _compute_signature(secret, msg_id, timestamp, payload)
            wrong_secret = inp["wrongSecret"]
            result = _verify_signature(wrong_secret, msg_id, timestamp, payload, sig)
            assert result == expect["verifies"], case["id"]

        elif action == "sign_twice_compare":
            sig1 = _compute_signature(secret, msg_id, timestamp, payload)
            sig2 = _compute_signature(secret, msg_id, timestamp, payload)
            assert (sig1 == sig2) == expect["identical"], case["id"]

        elif action == "verify_known_signature":
            sig = _compute_signature(secret, msg_id, timestamp, payload)
            expected_header = expect["signatureHeader"]
            # The expected header format is "v1,{timestamp},{sig_b64}"
            # Extract the signature part (after "v1,{timestamp},")
            expected_sig = expected_header.split(",", 2)[2] if expected_header.count(",") >= 2 else None
            actual_sig = sig.split(",", 1)[1]
            if expected_sig is not None:
                assert actual_sig == expected_sig, (
                    f"{case['id']}: expected sig {expected_sig}, got {actual_sig}"
                )
            else:
                pytest.fail(f"Could not parse expected signature header: {expected_header}")

        else:
            pytest.skip(f"Unknown action: {action}")
