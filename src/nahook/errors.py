"""Error classes for the Nahook SDK."""

from __future__ import annotations

from typing import Optional


class NahookError(Exception):
    """Base error for all SDK errors."""

    pass


class NahookAPIError(NahookError):
    """API returned an error response (4xx/5xx)."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.retry_after = retry_after

    @property
    def is_retryable(self) -> bool:
        return self.status >= 500 or self.status == 429

    @property
    def is_auth_error(self) -> bool:
        return self.status == 401 or (
            self.status == 403 and self.code == "token_disabled"
        )

    @property
    def is_not_found(self) -> bool:
        return self.status == 404

    @property
    def is_rate_limited(self) -> bool:
        return self.status == 429

    @property
    def is_validation_error(self) -> bool:
        return self.status == 400


class NahookNetworkError(NahookError):
    """Network-level failure (no HTTP response received)."""

    def __init__(self, cause: Exception) -> None:
        super().__init__(f"Network error: {cause}")
        self.cause = cause


class NahookTimeoutError(NahookError):
    """Request timed out."""

    def __init__(self, timeout_ms: float) -> None:
        super().__init__(f"Request timed out after {timeout_ms}ms")
        self.timeout_ms = timeout_ms
