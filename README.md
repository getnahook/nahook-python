# nahook

Official Python SDK for the [Nahook](https://nahook.com) webhook platform.

Two classes, one package:

| Class | Purpose | Auth |
|-------|---------|------|
| [`NahookClient`](#nahookclient) | Send and trigger webhook events | API key (`nhk_us_...`) |
| [`NahookManagement`](#nahookmanagement) | Manage endpoints, event types, apps | Management token (`nhm_...`) |

## Requirements

- Python 3.9+
- [httpx](https://www.python-httpx.org/) (installed automatically)

## Installation

```bash
pip install nahook
```

---

## NahookClient

Send webhooks to specific endpoints or fan-out by event type.

### Setup

```python
from nahook import NahookClient

client = NahookClient("nhk_us_...", retries=3, timeout=5_000, base_url="...")
# retries: default 0 (no retries)
# timeout: default 30_000ms
# base_url: default https://api.nahook.com
```

### Send to a specific endpoint

```python
result = client.send("ep_abc123", {
    "orderId": "123",
    "status": "paid",
}, idempotency_key="order-123-paid")  # optional, auto-generated UUID if omitted

# {"deliveryId": "del_...", "idempotencyKey": "order-123-paid", "status": "accepted"}
```

### Fan-out by event type

```python
result = client.trigger("order.paid", {
    "orderId": "123",
    "status": "paid",
}, metadata={"region": "us-east-1"})  # optional

# {"eventTypeId": "evt_...", "deliveryIds": ["del_..."], "status": "accepted"}
```

### Batch operations

```python
# Send to multiple endpoints (max 20 items)
batch = client.send_batch([
    {"endpointId": "ep_abc", "payload": {"orderId": "123"}},
    {"endpointId": "ep_def", "payload": {"orderId": "456"}},
])

# Fan-out multiple event types (max 20 items)
fan_out = client.trigger_batch([
    {"eventType": "order.paid", "payload": {"orderId": "123"}},
    {"eventType": "order.shipped", "payload": {"orderId": "456"}},
])

# Results: 202 (all succeed) or 207 (mixed)
for item in batch["items"]:
    if "error" in item:
        print(f"Item {item['index']} failed: {item['error']['code']}")
```

### Retry behavior

Retries are opt-in via the `retries` constructor parameter. When enabled:

- **Strategy:** Exponential backoff with full jitter
- **Delays:** 500ms base, 10s max
- **Retryable:** 5xx, 429 (respects `Retry-After`), network errors, timeouts
- **Non-retryable:** 400, 401, 403, 404, 409, 413
- **Safe by design:** Idempotency keys are always sent, making retries safe

---

## NahookManagement

Programmatically manage your Nahook workspace resources.

### Setup

```python
from nahook import NahookManagement

mgmt = NahookManagement("nhm_...", timeout=10_000, base_url="...")
# Note: retries are not supported for management calls
```

### Endpoints

```python
result = mgmt.endpoints.list("ws_abc")
endpoints = result["data"]

endpoint = mgmt.endpoints.create("ws_abc",
    url="https://example.com/webhooks",
    description="Production webhook",
    type_="webhook",  # "webhook" | "slack"
    metadata={"team": "payments"},
)

endpoint = mgmt.endpoints.get("ws_abc", "ep_123")

mgmt.endpoints.update("ws_abc", "ep_123",
    description="Updated",
    is_active=False,
)

mgmt.endpoints.delete("ws_abc", "ep_123")
```

### Event Types

```python
result = mgmt.event_types.list("ws_abc")

event_type = mgmt.event_types.create("ws_abc",
    name="order.paid",
    description="Fired when an order is paid",
)

event_type = mgmt.event_types.get("ws_abc", "evt_123")

mgmt.event_types.update("ws_abc", "evt_123",
    description="Updated description",
)

mgmt.event_types.delete("ws_abc", "evt_123")
```

### Applications

```python
result = mgmt.applications.list("ws_abc", limit=50, offset=0)

app = mgmt.applications.create("ws_abc",
    name="Acme Corp",
    external_id="acme-123",
    metadata={"tier": "pro"},
)

app = mgmt.applications.get("ws_abc", "app_123")

mgmt.applications.update("ws_abc", "app_123", name="Acme Inc")

mgmt.applications.delete("ws_abc", "app_123")

# Endpoints scoped to an application
result = mgmt.applications.list_endpoints("ws_abc", "app_123")
ep = mgmt.applications.create_endpoint("ws_abc", "app_123",
    url="https://acme.com/webhooks",
)
```

### Subscriptions

```python
result = mgmt.subscriptions.list("ws_abc", "ep_123")

mgmt.subscriptions.create("ws_abc", "ep_123", event_type_ids=["evt_456"])

mgmt.subscriptions.delete("ws_abc", "ep_123", "evt_456")
```

### Portal Sessions

```python
session = mgmt.portal_sessions.create("ws_abc", "app_123",
    metadata={"userId": "user-456"},
)
# session["url"]        -> redirect end-user here
# session["code"]       -> one-time exchange code
# session["expiresAt"]  -> expiration timestamp
```

---

## Error Handling

All SDK errors extend `NahookError`. Three specific types cover every failure mode:

```python
from nahook import NahookAPIError, NahookNetworkError, NahookTimeoutError

try:
    client.send("ep_abc", {"key": "value"})
except NahookAPIError as err:
    # API returned an error response
    print(err.status)        # 404
    print(err.code)          # "not_found"
    print(str(err))          # "Endpoint not found"
    print(err.retry_after)   # seconds (on 429s)

    # Convenience checks
    err.is_retryable       # True for 5xx, 429
    err.is_auth_error      # True for 401, 403 (token_disabled)
    err.is_not_found       # True for 404
    err.is_rate_limited    # True for 429
    err.is_validation_error  # True for 400
except NahookNetworkError as err:
    print(err.cause)  # original httpx error
except NahookTimeoutError as err:
    print(err.timeout_ms)  # timeout that was exceeded
```

---

## Webhook Verification

Nahook signs outgoing deliveries using the [Standard Webhooks](https://www.standardwebhooks.com/) specification. Use the `standardwebhooks` package to verify incoming webhooks:

```bash
pip install standardwebhooks
```

```python
from standardwebhooks import Webhook

wh = Webhook("whsec_MfKQ9r8GKYqr...")

try:
    payload = wh.verify(request.body, request.headers)
    # Verified and safe to use
except Exception:
    # Invalid signature
    pass
```

The signing secret (`whsec_...`) is available in your Nahook Dashboard endpoint settings.

---

## Development

```bash
pip install -e ".[dev]"   # install with dev dependencies
pytest                     # run tests
```

## License

MIT
