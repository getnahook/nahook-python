"""HTTP client with retry logic for the Nahook SDK."""

from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, Literal, Optional, Tuple
from urllib.parse import quote

import httpx

from .errors import NahookAPIError, NahookNetworkError, NahookTimeoutError

DEFAULT_BASE_URL = "https://api.nahook.com"
DEFAULT_TIMEOUT_MS = 30_000
SDK_VERSION = "0.1.0"
USER_AGENT = f"nahook-python/{SDK_VERSION}"

BASE_DELAY_MS = 500
MAX_DELAY_MS = 10_000


def _calculate_delay(attempt: int, retry_after_ms: Optional[float] = None) -> float:
    """Exponential backoff with full jitter."""
    if retry_after_ms and retry_after_ms > 0:
        return retry_after_ms
    exponential = min(MAX_DELAY_MS, BASE_DELAY_MS * math.pow(2, attempt))
    return exponential * random.random()


def _is_retryable(error: Exception) -> bool:
    """Whether an error is retryable."""
    if isinstance(error, NahookAPIError):
        return error.is_retryable
    return isinstance(error, (NahookNetworkError, NahookTimeoutError))


class HttpClient:
    """Low-level HTTP client with retry support."""

    def __init__(
        self,
        token: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: int = 0,
    ) -> None:
        self._token = token
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_MS
        self._retries = retries
        self._client = httpx.Client(timeout=self._timeout / 1000)

    def request(
        self,
        method: Literal["GET", "POST", "PATCH", "DELETE"],
        path: str,
        body: Any = None,
        query: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute an HTTP request and return the parsed JSON response."""
        response = self._execute_with_retry(method, path, body, query)
        return self._handle_response(response)

    def request_with_status(
        self,
        method: Literal["GET", "POST", "PATCH", "DELETE"],
        path: str,
        body: Any = None,
        query: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Any]:
        """Execute a request and return (status_code, data)."""
        response = self._execute_with_retry(method, path, body, query)
        if 200 <= response.status_code < 300:
            return response.status_code, response.json()
        raise self._parse_error(response)

    def _execute_with_retry(
        self,
        method: str,
        path: str,
        body: Any,
        query: Optional[Dict[str, Any]],
    ) -> httpx.Response:
        url = self._build_url(path, query)
        has_body = body is not None

        headers: Dict[str, str] = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        if has_body:
            headers["Content-Type"] = "application/json"

        last_error: Optional[Exception] = None

        for attempt in range(self._retries + 1):
            if attempt > 0 and last_error is not None:
                retry_after_ms: Optional[float] = None
                if isinstance(last_error, NahookAPIError) and last_error.retry_after:
                    retry_after_ms = last_error.retry_after * 1000
                delay = _calculate_delay(attempt - 1, retry_after_ms)
                time.sleep(delay / 1000)

            try:
                response = self._fetch(method, url, headers, body if has_body else None)

                if not (200 <= response.status_code < 300):
                    error = self._parse_error(response)
                    if attempt < self._retries and _is_retryable(error):
                        last_error = error
                        continue
                    raise error

                return response
            except (NahookAPIError, NahookNetworkError, NahookTimeoutError) as error:
                last_error = error
                if attempt < self._retries and _is_retryable(error):
                    continue
                raise

        # Unreachable, but satisfies type checker
        assert last_error is not None
        raise last_error

    def _fetch(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Any,
    ) -> httpx.Response:
        try:
            response = self._client.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
            )
            return response
        except httpx.TimeoutException:
            raise NahookTimeoutError(self._timeout)
        except httpx.HTTPError as exc:
            raise NahookNetworkError(exc)

    def _handle_response(self, response: httpx.Response) -> Any:
        if 200 <= response.status_code < 300:
            if response.status_code == 204:
                return None
            return response.json()
        raise self._parse_error(response)

    def _parse_error(self, response: httpx.Response) -> NahookAPIError:
        retry_after_str = response.headers.get("retry-after")
        retry_after: Optional[int] = None
        if retry_after_str:
            try:
                retry_after = int(retry_after_str)
            except ValueError:
                pass

        try:
            data = response.json()
            error_obj = data.get("error", {}) if isinstance(data, dict) else {}
            code = error_obj.get("code", "unknown")
            message = error_obj.get("message", response.reason_phrase or "Unknown error")
        except Exception:
            code = "unknown"
            message = response.reason_phrase or "Unknown error"

        return NahookAPIError(response.status_code, code, message, retry_after)

    def _build_url(
        self, path: str, query: Optional[Dict[str, Any]] = None
    ) -> str:
        url = f"{self._base_url}{path}"
        if query:
            filtered = {k: str(v) for k, v in query.items() if v is not None}
            if filtered:
                qs = "&".join(f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in filtered.items())
                url = f"{url}?{qs}"
        return url
