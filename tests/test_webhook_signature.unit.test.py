"""
Webhook signature verification tests.

Validates that the Standard Webhooks signing format used by the Nahook API
can be correctly produced and verified using native crypto.

Signing spec:
    base   = "{msgId}.{timestamp}.{payload}"
    key    = base64_decode(secret_without_whsec_prefix)
    sig    = "v1," + base64(HMAC-SHA256(key, base))
    headers: webhook-id, webhook-timestamp, webhook-signature
"""

import base64
import hashlib
import hmac
import re


TEST_SECRET = "whsec_dGVzdF93ZWJob29rX3NpZ25pbmdfa2V5XzMyYnl0ZXMh"
MSG_ID = "msg_test_sig_001"
TIMESTAMP = "1712345678"
PAYLOAD = '{"order_id":"ord_123","amount":49.99}'


def compute_signature(secret: str, msg_id: str, timestamp: str, payload: str) -> str:
    raw_secret = secret[6:] if secret.startswith("whsec_") else secret
    key = base64.b64decode(raw_secret)
    to_sign = f"{msg_id}.{timestamp}.{payload}".encode()
    digest = hmac.new(key, to_sign, hashlib.sha256).digest()
    return f"v1,{base64.b64encode(digest).decode()}"


def test_produces_valid_v1_signature():
    sig = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    assert re.match(r"^v1,[A-Za-z0-9+/]+=*$", sig)


def test_deterministic_same_inputs_same_signature():
    sig1 = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    sig2 = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    assert sig1 == sig2


def test_rejects_tampered_payload():
    original = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    tampered = compute_signature(
        TEST_SECRET, MSG_ID, TIMESTAMP, '{"order_id":"ord_123","amount":99.99}'
    )
    assert original != tampered


def test_rejects_wrong_secret():
    original = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    wrong = compute_signature("whsec_d3Jvbmdfc2VjcmV0", MSG_ID, TIMESTAMP, PAYLOAD)
    assert original != wrong


def test_rejects_tampered_msg_id():
    original = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    tampered = compute_signature(TEST_SECRET, "msg_tampered_id", TIMESTAMP, PAYLOAD)
    assert original != tampered


def test_rejects_tampered_timestamp():
    original = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    tampered = compute_signature(TEST_SECRET, MSG_ID, "9999999999", PAYLOAD)
    assert original != tampered


def test_correct_headers_structure():
    sig = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    headers = {
        "content-type": "application/json",
        "webhook-id": MSG_ID,
        "webhook-timestamp": TIMESTAMP,
        "webhook-signature": sig,
    }
    assert headers["webhook-id"].startswith("msg_")
    assert headers["webhook-timestamp"].isdigit()
    assert headers["webhook-signature"].startswith("v1,")
    assert headers["content-type"] == "application/json"


def test_handles_secret_without_prefix():
    raw_secret = TEST_SECRET[6:]
    with_prefix = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    without_prefix = compute_signature(raw_secret, MSG_ID, TIMESTAMP, PAYLOAD)
    assert with_prefix == without_prefix


def test_matches_known_cross_language_reference_signature():
    sig = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, PAYLOAD)
    assert sig == "v1,VF1JBS4kdSwmE64FeeiWTgszlPCfaop53x8bwzvHizw="


def test_empty_payload_produces_valid_signature():
    sig = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, "")
    assert sig == "v1,yNFeVvBSs4aZ/sVHHw1MaUWnN1IGK/Ul/16T8aptSJo="


def test_unicode_payload_consistent_across_languages():
    sig = compute_signature(TEST_SECRET, MSG_ID, TIMESTAMP, '{"name":"café","price":"€9.99"}')
    assert sig == "v1,GcuGAMV9tELnF2rjay6sA8uo5PDPPlhaFi6gKUg06wQ="
