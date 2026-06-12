"""Type definitions for the Nahook SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

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
    subscriberCount: int
    createdAt: str


class _Unset:
    """Sentinel distinguishing "argument not passed" from an explicit ``None``.

    Used for tri-state PATCH fields like ``max_endpoints``: leaving the
    argument as ``UNSET`` omits it from the request body (unchanged), while
    passing ``None`` sends an explicit JSON null (clear).
    """

    _instance: Optional["_Unset"] = None

    def __new__(cls) -> "_Unset":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET = _Unset()


class Application(TypedDict):
    id: str
    externalId: Optional[str]
    name: str
    metadata: Dict[str, str]
    maxEndpoints: Optional[int]
    showEventTypes: bool
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


# ── Deliveries ──


DeliveryStatus = Literal[
    "pending",
    "delivering",
    "delivered",
    "scheduled_retry",
    "failed",
    "dead_letter",
]


class Delivery(TypedDict):
    """Metadata for a single webhook delivery."""

    id: str
    idempotencyKey: str
    endpointId: str
    status: DeliveryStatus
    totalAttempts: int
    firstAttemptAt: Optional[str]
    deliveredAt: Optional[str]
    nextRetryAt: Optional[str]
    hasPayload: bool
    createdAt: str
    updatedAt: str


class DeliveryAttempt(TypedDict):
    """A single delivery attempt record."""

    id: str
    attemptNumber: int
    status: str
    responseStatusCode: Optional[int]
    responseTimeMs: Optional[int]
    errorMessage: Optional[str]
    createdAt: str


class PayloadEnvelopeAvailable(TypedDict):
    """Envelope returned when the stored payload could be read and decrypted."""

    status: Literal["available"]
    data: Any
    contentType: str


class PayloadEnvelopeForbidden(TypedDict):
    """Envelope returned when the workspace plan does not include payload storage."""

    status: Literal["forbidden"]


class PayloadEnvelopeProcessing(TypedDict):
    """Envelope returned when the delivery is still in flight."""

    status: Literal["processing"]


class PayloadEnvelopeNotFound(TypedDict):
    """Envelope returned when no stored payload exists for a terminal delivery."""

    status: Literal["not_found"]


class PayloadEnvelopeError(TypedDict):
    """Envelope returned on transient infrastructure failures."""

    status: Literal["error"]


PayloadEnvelope = Union[
    PayloadEnvelopeAvailable,
    PayloadEnvelopeForbidden,
    PayloadEnvelopeProcessing,
    PayloadEnvelopeNotFound,
    PayloadEnvelopeError,
]


class DeliveryWithPayload(Delivery, total=False):
    """Delivery metadata, optionally extended with a payload envelope.

    The ``payload`` key is present only when the caller passes
    ``include_payload=True`` to ``get()``. Inspect ``payload["status"]`` to
    branch on availability — only ``"available"`` carries ``data``.
    """

    payload: PayloadEnvelope


class PaginatedResult(TypedDict):
    """A page of results plus an opaque cursor for the next page.

    Conceptually parameterised on the item type (``data: list[T]``); spelled
    here as ``List[Any]`` because Generic ``TypedDict`` is only available on
    Python 3.11+ and this package supports 3.9. The concrete item type for
    each call site is documented on the returning method.

    ``next_cursor`` is ``None`` when there are no further pages — never absent.
    Pass it back verbatim to fetch the next page; it is opaque and may change
    encoding without notice.
    """

    data: List[Any]
    next_cursor: Optional[str]


class ListDeliveriesOptions(TypedDict, total=False):
    """Optional filters for ``deliveries.list()``."""

    limit: int
    cursor: str
    status: DeliveryStatus


class GetDeliveryOptions(TypedDict, total=False):
    """Optional flags for ``deliveries.get()``."""

    include_payload: bool
