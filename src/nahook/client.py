"""NahookClient for sending and triggering webhook events."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .http_client import HttpClient
from .types import BatchResult, SendResult, TriggerResult


class NahookClient:
    """Send webhooks to specific endpoints or fan-out by event type.

    Args:
        api_key: API key starting with ``nhk_``.
        base_url: Override the default API base URL.
        timeout: Request timeout in milliseconds (default 30000).
        retries: Number of retries on retryable failures (default 0).
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: int = 0,
    ) -> None:
        if not api_key.startswith("nhk_"):
            raise ValueError("Invalid API key: must start with 'nhk_'")
        self._http = HttpClient(
            token=api_key,
            base_url=base_url,
            timeout=timeout,
            retries=retries,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "NahookClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def send(
        self,
        endpoint_id: str,
        payload: Dict[str, Any],
        *,
        idempotency_key: Optional[str] = None,
    ) -> SendResult:
        """Send a payload to a specific endpoint.

        Args:
            endpoint_id: Target endpoint ID (e.g. ``ep_abc``).
            payload: JSON-serializable payload.
            idempotency_key: Optional deduplication key; auto-generated UUID if omitted.
        """
        key = idempotency_key if idempotency_key is not None else str(uuid.uuid4())
        return self._http.request(
            "POST",
            f"/api/ingest/{quote(endpoint_id, safe='')}",
            body={
                "payload": payload,
                "idempotencyKey": key,
            },
        )

    def trigger(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        metadata: Optional[Dict[str, str]] = None,
    ) -> TriggerResult:
        """Fan-out a payload by event type to all subscribed endpoints.

        Args:
            event_type: Event type name (e.g. ``order.paid``).
            payload: JSON-serializable payload.
            metadata: Optional metadata dict.
        """
        body: Dict[str, Any] = {"payload": payload}
        if metadata is not None:
            body["metadata"] = metadata
        return self._http.request(
            "POST",
            f"/api/ingest/event/{quote(event_type, safe='')}",
            body=body,
        )

    def send_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> BatchResult:
        """Batch send to multiple specific endpoints (max 20 items).

        Each item should have ``endpointId``, ``payload``, and optionally ``idempotencyKey``.
        """
        _, data = self._http.request_with_status(
            "POST",
            "/api/ingest/batch",
            body={"items": items},
        )
        return data

    def trigger_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> BatchResult:
        """Batch fan-out by event types (max 20 items).

        Each item should have ``eventType``, ``payload``, and optionally ``metadata``.
        """
        _, data = self._http.request_with_status(
            "POST",
            "/api/ingest/event/batch",
            body={"items": items},
        )
        return data
