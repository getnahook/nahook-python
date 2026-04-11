"""Environments management resource."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

from ..http_client import HttpClient
from ..types import Environment, EventTypeVisibility, ListResult


class EnvironmentsResource:
    """Manage workspace environments."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def _base(self, workspace_id: str) -> str:
        return f"/management/v1/workspaces/{quote(workspace_id, safe='')}/environments"

    def list(self, workspace_id: str) -> ListResult:
        data = self._http.request("GET", self._base(workspace_id))
        return {"data": data}

    def create(
        self,
        workspace_id: str,
        *,
        name: str,
        slug: str,
    ) -> Environment:
        body: Dict[str, Any] = {"name": name, "slug": slug}
        return self._http.request("POST", self._base(workspace_id), body=body)

    def get(self, workspace_id: str, environment_id: str) -> Environment:
        return self._http.request(
            "GET",
            f"{self._base(workspace_id)}/{quote(environment_id, safe='')}",
        )

    def update(
        self,
        workspace_id: str,
        environment_id: str,
        *,
        name: Optional[str] = None,
    ) -> Environment:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        return self._http.request(
            "PATCH",
            f"{self._base(workspace_id)}/{quote(environment_id, safe='')}",
            body=body,
        )

    def delete(self, workspace_id: str, environment_id: str) -> None:
        self._http.request(
            "DELETE",
            f"{self._base(workspace_id)}/{quote(environment_id, safe='')}",
        )

    def list_event_type_visibility(
        self, workspace_id: str, environment_id: str
    ) -> ListResult:
        data = self._http.request(
            "GET",
            f"{self._base(workspace_id)}/{quote(environment_id, safe='')}/event-types",
        )
        return {"data": data}

    def set_event_type_visibility(
        self,
        workspace_id: str,
        environment_id: str,
        event_type_id: str,
        *,
        published: bool,
    ) -> EventTypeVisibility:
        return self._http.request(
            "PUT",
            f"{self._base(workspace_id)}/{quote(environment_id, safe='')}/event-types/{quote(event_type_id, safe='')}/visibility",
            body={"published": published},
        )
