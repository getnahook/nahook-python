"""Error classification tests for NahookAPIError, NahookNetworkError, NahookTimeoutError."""

import unittest

from nahook.errors import NahookAPIError, NahookNetworkError, NahookTimeoutError


class TestAPIErrorRetryable(unittest.TestCase):
    def test_retryable_on_500(self):
        error = NahookAPIError(500, "internal_error", "Server error")
        assert error.is_retryable

    def test_retryable_on_429(self):
        error = NahookAPIError(429, "rate_limited", "Too many requests", retry_after=5)
        assert error.is_retryable

    def test_not_retryable_on_404(self):
        error = NahookAPIError(404, "not_found", "Not found")
        assert not error.is_retryable


class TestAPIErrorAuthError(unittest.TestCase):
    def test_auth_error_on_401(self):
        error = NahookAPIError(401, "unauthorized", "Invalid token")
        assert error.is_auth_error

    def test_auth_error_on_403_token_disabled(self):
        error = NahookAPIError(403, "token_disabled", "Token disabled")
        assert error.is_auth_error

    def test_not_auth_error_on_403_other(self):
        error = NahookAPIError(403, "forbidden", "Forbidden")
        assert not error.is_auth_error


class TestAPIErrorNotFound(unittest.TestCase):
    def test_not_found_on_404(self):
        error = NahookAPIError(404, "not_found", "Resource not found")
        assert error.is_not_found

    def test_not_not_found_on_500(self):
        error = NahookAPIError(500, "internal_error", "Server error")
        assert not error.is_not_found


class TestAPIErrorRateLimited(unittest.TestCase):
    def test_rate_limited_on_429(self):
        error = NahookAPIError(429, "rate_limited", "Too many requests", retry_after=10)
        assert error.is_rate_limited
        assert error.retry_after == 10

    def test_not_rate_limited_on_500(self):
        error = NahookAPIError(500, "internal_error", "Server error")
        assert not error.is_rate_limited


class TestAPIErrorValidation(unittest.TestCase):
    def test_validation_error_on_400(self):
        error = NahookAPIError(400, "validation_error", "Bad request")
        assert error.is_validation_error

    def test_not_validation_error_on_401(self):
        error = NahookAPIError(401, "unauthorized", "Unauthorized")
        assert not error.is_validation_error


class TestNetworkError(unittest.TestCase):
    def test_wraps_original_cause(self):
        cause = ConnectionError("connection refused")
        error = NahookNetworkError(cause)
        assert error.cause is cause
        assert "connection refused" in str(error)


class TestTimeoutError(unittest.TestCase):
    def test_stores_timeout_ms(self):
        error = NahookTimeoutError(15000)
        assert error.timeout_ms == 15000
        assert "15000ms" in str(error)
