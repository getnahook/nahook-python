"""Deliveries management resource."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

from ..http_client import HttpClient
from ..types import (
    Delivery,
    DeliveryAttempt,
    DeliveryWithPayload,
    PaginatedResult,
)


class DeliveriesResource:
    """Read access to a workspace's webhook deliveries.

    All methods are paginated or single-resource reads — there is no
    create/update/delete on this resource. ``list()`` is endpoint-scoped
    because the regional deliveries table is indexed by endpoint; there
    is no workspace-wide index. ``get()`` and ``get_attempts()`` accept a
    delivery public id directly.
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        workspace_id: str,
        endpoint_id: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        status: Optional[str] = None,
    ) -> PaginatedResult:
        """List deliveries for an endpoint, newest-first.

        :param workspace_id: Workspace public id (``ws_…``).
        :param endpoint_id: Endpoint public id (``ep_…``).
        :param limit: Optional. Page size; server caps at 100, defaults to 50.
        :param cursor: Optional. Opaque token from a previous ``next_cursor``.
            Pass through verbatim — do not decode or modify.
        :param status: Optional. One of ``pending``, ``delivering``,
            ``delivered``, ``scheduled_retry``, ``failed``, ``dead_letter``.

        :returns: ``PaginatedResult`` with:

            * ``data``: list of ``Delivery`` items (renamed from the wire
              field ``deliveries`` for cross-SDK consistency).
            * ``next_cursor``: opaque string for the next page, or ``None``
              when there are no more pages.
        """
        query: Dict[str, Any] = {}
        if limit is not None:
            query["limit"] = limit
        if cursor is not None:
            query["cursor"] = cursor
        if status is not None:
            query["status"] = status

        raw = self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}"
            f"/endpoints/{quote(endpoint_id, safe='')}/deliveries",
            query=query if query else None,
        )
        deliveries: List[Delivery] = raw.get("deliveries", []) if isinstance(raw, dict) else []
        next_cursor = raw.get("nextCursor") if isinstance(raw, dict) else None
        return {"data": deliveries, "next_cursor": next_cursor}

    def get(
        self,
        workspace_id: str,
        delivery_id: str,
        *,
        include_payload: bool = False,
    ) -> DeliveryWithPayload:
        """Fetch a single delivery's metadata.

        :param include_payload: When ``True``, the response includes a
            ``payload`` envelope. Inspect ``payload["status"]`` to branch:

            * ``"available"`` — ``data`` and ``contentType`` are present.
            * ``"forbidden"`` — workspace plan does not include payload
              storage.
            * ``"processing"`` — delivery still in flight.
            * ``"not_found"`` — terminal delivery without a stored payload.
            * ``"error"`` — transient infrastructure failure.

            The HTTP call returns 200 for all five envelope states; do not
            treat ``forbidden`` / ``processing`` / ``not_found`` / ``error``
            as exceptions.
        """
        query: Optional[Dict[str, Any]] = {"include": "payload"} if include_payload else None
        return self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}"
            f"/deliveries/{quote(delivery_id, safe='')}",
            query=query,
        )

    def get_attempts(
        self, workspace_id: str, delivery_id: str
    ) -> List[DeliveryAttempt]:
        """List a delivery's attempts in chronological order (oldest first)."""
        return self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}"
            f"/deliveries/{quote(delivery_id, safe='')}/attempts",
        )
