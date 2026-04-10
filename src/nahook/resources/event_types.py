"""Event types management resource."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

from ..http_client import HttpClient
from ..types import EventType, ListResult


class EventTypesResource:
    """Manage event types."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, workspace_id: str) -> ListResult:
        data = self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/event-types",
        )
        return {"data": data}

    def create(
        self,
        workspace_id: str,
        *,
        name: str,
        description: Optional[str] = None,
    ) -> EventType:
        body: Dict[str, Any] = {"name": name}
        if description is not None:
            body["description"] = description
        return self._http.request(
            "POST",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/event-types",
            body=body,
        )

    def get(self, workspace_id: str, event_type_id: str) -> EventType:
        return self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/event-types/{quote(event_type_id, safe='')}",
        )

    def update(
        self,
        workspace_id: str,
        event_type_id: str,
        *,
        description: Optional[str] = None,
    ) -> EventType:
        body: Dict[str, Any] = {}
        if description is not None:
            body["description"] = description
        return self._http.request(
            "PATCH",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/event-types/{quote(event_type_id, safe='')}",
            body=body,
        )

    def delete(self, workspace_id: str, event_type_id: str) -> None:
        self._http.request(
            "DELETE",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/event-types/{quote(event_type_id, safe='')}",
        )
