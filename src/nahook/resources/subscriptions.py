"""Subscriptions management resource."""

from __future__ import annotations

from urllib.parse import quote

from ..http_client import HttpClient
from ..types import ListResult, Subscription


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
        event_type_id: str,
    ) -> Subscription:
        return self._http.request(
            "POST",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints/{quote(endpoint_id, safe='')}/subscriptions",
            body={"eventTypeId": event_type_id},
        )

    def delete(
        self, workspace_id: str, endpoint_id: str, event_type_id: str
    ) -> None:
        self._http.request(
            "DELETE",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints/{quote(endpoint_id, safe='')}/subscriptions/{quote(event_type_id, safe='')}",
        )
