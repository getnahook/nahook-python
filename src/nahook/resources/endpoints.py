"""Endpoints management resource."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

from ..http_client import HttpClient
from ..types import Endpoint, ListResult


class EndpointsResource:
    """Manage webhook endpoints."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, workspace_id: str) -> ListResult:
        data = self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints",
        )
        return {"data": data}

    def create(
        self,
        workspace_id: str,
        *,
        url: str,
        type_: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        config: Optional[Dict[str, Any]] = None,
        auth_username: Optional[str] = None,
        auth_password: Optional[str] = None,
    ) -> Endpoint:
        body: Dict[str, Any] = {"url": url}
        if type_ is not None:
            body["type"] = type_
        if description is not None:
            body["description"] = description
        if metadata is not None:
            body["metadata"] = metadata
        if config is not None:
            body["config"] = config
        if auth_username is not None:
            body["authUsername"] = auth_username
        if auth_password is not None:
            body["authPassword"] = auth_password
        return self._http.request(
            "POST",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints",
            body=body,
        )

    def get(self, workspace_id: str, id: str) -> Endpoint:
        return self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints/{quote(id, safe='')}",
        )

    def update(
        self,
        workspace_id: str,
        id: str,
        *,
        url: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        is_active: Optional[bool] = None,
    ) -> Endpoint:
        body: Dict[str, Any] = {}
        if url is not None:
            body["url"] = url
        if description is not None:
            body["description"] = description
        if metadata is not None:
            body["metadata"] = metadata
        if is_active is not None:
            body["isActive"] = is_active
        return self._http.request(
            "PATCH",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints/{quote(id, safe='')}",
            body=body,
        )

    def delete(self, workspace_id: str, id: str) -> None:
        self._http.request(
            "DELETE",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/endpoints/{quote(id, safe='')}",
        )
