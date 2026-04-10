"""Applications management resource."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

from ..http_client import HttpClient
from ..types import Application, Endpoint, ListResult


class ApplicationsResource:
    """Manage applications."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        workspace_id: str,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResult:
        data = self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/applications",
            query={"limit": limit, "offset": offset},
        )
        return {"data": data}

    def create(
        self,
        workspace_id: str,
        *,
        name: str,
        external_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Application:
        body: Dict[str, Any] = {"name": name}
        if external_id is not None:
            body["externalId"] = external_id
        if metadata is not None:
            body["metadata"] = metadata
        return self._http.request(
            "POST",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/applications",
            body=body,
        )

    def get(self, workspace_id: str, id: str) -> Application:
        return self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/applications/{quote(id, safe='')}",
        )

    def update(
        self,
        workspace_id: str,
        id: str,
        *,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Application:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if metadata is not None:
            body["metadata"] = metadata
        return self._http.request(
            "PATCH",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/applications/{quote(id, safe='')}",
            body=body,
        )

    def delete(self, workspace_id: str, id: str) -> None:
        self._http.request(
            "DELETE",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/applications/{quote(id, safe='')}",
        )

    def list_endpoints(
        self, workspace_id: str, app_id: str
    ) -> ListResult:
        data = self._http.request(
            "GET",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/applications/{quote(app_id, safe='')}/endpoints",
        )
        return {"data": data}

    def create_endpoint(
        self,
        workspace_id: str,
        app_id: str,
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
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/applications/{quote(app_id, safe='')}/endpoints",
            body=body,
        )
