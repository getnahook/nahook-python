"""Type definitions for the Nahook SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


# ── Client (ingestion) types ──


class SendResult(TypedDict):
    deliveryId: str
    idempotencyKey: str
    status: Literal["accepted"]


class TriggerResult(TypedDict):
    eventTypeId: str
    deliveryIds: List[str]
    status: Literal["accepted"]


class BatchResultItem(TypedDict, total=False):
    index: int  # required in practice
    deliveryId: str
    idempotencyKey: str
    eventTypeId: str
    deliveryIds: List[str]
    status: Literal["accepted"]
    error: Dict[str, str]


class BatchResult(TypedDict):
    items: List[BatchResultItem]


# ── Management types ──


class Endpoint(TypedDict, total=False):
    id: str  # required
    url: str  # required
    description: Optional[str]
    isActive: bool
    type: Literal["webhook", "slack"]
    config: Dict[str, Any]
    secret: str
    metadata: Dict[str, str]
    createdAt: str
    updatedAt: str


class EventType(TypedDict):
    id: str
    name: str
    description: Optional[str]
    createdAt: str


class Application(TypedDict):
    id: str
    externalId: Optional[str]
    name: str
    metadata: Dict[str, str]
    createdAt: str
    updatedAt: str


class Subscription(TypedDict):
    id: str
    eventTypeId: str
    eventTypeName: str
    createdAt: str


class SubscribeResult(TypedDict):
    subscribed: int


class PortalSession(TypedDict):
    url: str
    code: str
    expiresAt: str


class Environment(TypedDict):
    id: str
    name: str
    slug: str
    isDefault: bool
    createdAt: str
    updatedAt: str


class CreateEnvironmentOptions(TypedDict):
    name: str
    slug: str


class UpdateEnvironmentOptions(TypedDict, total=False):
    name: str


class EventTypeVisibility(TypedDict):
    eventTypeId: str
    eventTypeName: str
    published: bool


class SetVisibilityOptions(TypedDict):
    published: bool


class ListResult(TypedDict):
    data: List[Any]
