"""Portal sessions management resource."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

from ..http_client import HttpClient
from ..types import PortalSession


class PortalSessionsResource:
    """Create portal sessions for end-user access."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        workspace_id: str,
        app_id: str,
        *,
        metadata: Optional[Dict[str, str]] = None,
    ) -> PortalSession:
        body: Dict[str, Any] = {}
        if metadata is not None:
            body["metadata"] = metadata
        return self._http.request(
            "POST",
            f"/management/v1/workspaces/{quote(workspace_id, safe='')}/applications/{quote(app_id, safe='')}/portal",
            body=body,
        )
