"""NahookManagement for managing workspace resources."""

from __future__ import annotations

from typing import Optional

from .http_client import HttpClient
from .resources.applications import ApplicationsResource
from .resources.endpoints import EndpointsResource
from .resources.event_types import EventTypesResource
from .resources.portal_sessions import PortalSessionsResource
from .resources.subscriptions import SubscriptionsResource


class NahookManagement:
    """Programmatically manage Nahook workspace resources.

    Args:
        token: Management token starting with ``nhm_``.
        base_url: Override the default API base URL.
        timeout: Request timeout in milliseconds (default 30000).
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        if not token.startswith("nhm_"):
            raise ValueError("Invalid management token: must start with 'nhm_'")
        http = HttpClient(
            token=token,
            base_url=base_url,
            timeout=timeout,
        )
        self.endpoints = EndpointsResource(http)
        self.event_types = EventTypesResource(http)
        self.applications = ApplicationsResource(http)
        self.subscriptions = SubscriptionsResource(http)
        self.portal_sessions = PortalSessionsResource(http)
