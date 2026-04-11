"""Subscriptions management resource."""

from __future__ import annotations

from typing import List
from urllib.parse import quote

from ..http_client import HttpClient
from ..types import ListResult, SubscribeResult


class SubscriptionsResource:
    """Manage endpoint subscriptions to event types."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self, workspace_id: str, endpoint_id: str
    ) -> ListResult:
        data = self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints/{quote(endpoint_id, safe='')}/subscriptions",
        )
        return {"data": data}

    def create(
        self,
        workspace_id: str,
        endpoint_id: str,
        *,
        event_type_ids: List[str],
    ) -> SubscribeResult:
        """Subscribe an endpoint to one or more event types.

        Args:
            workspace_id: Workspace public ID.
            endpoint_id: Endpoint public ID.
            event_type_ids: List of event type public IDs to subscribe to.

        Returns:
            A dict with ``{"subscribed": N}`` indicating how many were subscribed.
        """
        return self._http.request(
            "POST",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints/{quote(endpoint_id, safe='')}/subscriptions",
            body={"eventTypeIds": event_type_ids},
        )

    def delete(
        self, workspace_id: str, endpoint_id: str, event_type_id: str
    ) -> None:
        self._http.request(
            "DELETE",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints/{quote(endpoint_id, safe='')}/subscriptions/{quote(event_type_id, safe='')}",
        )
