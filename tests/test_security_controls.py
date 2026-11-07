import asyncio
import unittest

from pydantic import ValidationError

from app.core.rate_limit import (
    APIRateLimitMiddleware,
    SecurityHeadersMiddleware,
    SlidingWindowLimiter,
    clear_login_failures,
    login_failure_limiter,
    login_lockout_retry_after,
    record_login_failure,
    request_limiter,
)
from app.schemas.user import UserCreate


class PasswordPolicyTests(unittest.TestCase):
    def test_accepts_long_password_with_required_character_classes(self):
        user = UserCreate(
            username="testuser",
            full_name="Test User",
            password="Strong-Passphrase42",
        )

        self.assertEqual(user.password, "Strong-Passphrase42")

    def test_rejects_short_password(self):
        with self.assertRaises(ValidationError):
            UserCreate(
                username="testuser",
                full_name="Test User",
                password="Weakpass1!",
            )

    def test_rejects_common_password(self):
        with self.assertRaises(ValidationError):
            UserCreate(
                username="testuser",
                full_name="Test User",
                password="Password123!",
            )

    def test_rejects_password_over_bcrypt_byte_limit(self):
        with self.assertRaises(ValidationError):
            UserCreate(
                username="testuser",
                full_name="Test User",
                password="Aa1!" + "é" * 35,
            )


class RateLimitTests(unittest.TestCase):
    def test_request_window_rejects_requests_over_the_limit(self):
        limiter = SlidingWindowLimiter()
        key = ("api", "192.0.2.3")

        self.assertIsNone(limiter.consume(key, limit=2, window_seconds=60))
        self.assertIsNone(limiter.consume(key, limit=2, window_seconds=60))
        self.assertIsNotNone(limiter.consume(key, limit=2, window_seconds=60))

    def test_sliding_window_blocks_until_earliest_request_expires(self):
        limiter = SlidingWindowLimiter()
        key = ("api", "192.0.2.1")
        limiter.record(key, window_seconds=10, now=0.0)
        limiter.record(key, window_seconds=10, now=1.0)

        self.assertEqual(
            limiter.retry_after(key, limit=2, window_seconds=10, now=2.0),
            8,
        )
        self.assertIsNone(
            limiter.retry_after(key, limit=2, window_seconds=10, now=10.0)
        )

    def test_repeated_login_failures_are_temporarily_locked(self):
        client_ip = "192.0.2.2"
        username = "lockout-test-user"
        clear_login_failures(client_ip, username)
        login_failure_limiter.clear(("login-ip", client_ip))

        for _ in range(4):
            self.assertIsNone(
                record_login_failure(client_ip, username, failure_limit=5, lockout_seconds=60)
            )

        self.assertIsNotNone(
            record_login_failure(client_ip, username, failure_limit=5, lockout_seconds=60)
        )
        self.assertIsNotNone(
            login_lockout_retry_after(
                client_ip, username, failure_limit=5, lockout_seconds=60
            )
        )
        clear_login_failures(client_ip, username)
        login_failure_limiter.clear(("login-ip", client_ip))

    def test_api_middleware_returns_429_after_configured_limit(self):
        client_ip = "192.0.2.4"
        request_limiter.clear(("api", client_ip))

        async def app(_scope, _receive, send):
            await send(
                {"type": "http.response.start", "status": 200, "headers": []}
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"ok",
                    "more_body": False,
                }
            )

        middleware = APIRateLimitMiddleware(app, requests=1, window_seconds=60)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/ping",
            "client": (client_ip, 12345),
        }

        first_response = asyncio.run(self._call_asgi(middleware, scope))
        second_response = asyncio.run(self._call_asgi(middleware, scope))

        self.assertEqual(first_response[0]["status"], 200)
        self.assertEqual(second_response[0]["status"], 429)
        headers = dict(second_response[0]["headers"])
        self.assertGreater(int(headers[b"retry-after"]), 0)

    def test_security_headers_are_added_and_hsts_requires_https(self):
        async def app(_scope, _receive, send):
            await send(
                {"type": "http.response.start", "status": 200, "headers": []}
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"ok",
                    "more_body": False,
                }
            )

        middleware = SecurityHeadersMiddleware(app, production=True)
        https_scope = {"type": "http", "scheme": "https"}
        response = asyncio.run(self._call_asgi(middleware, https_scope))
        headers = dict(response[0]["headers"])

        self.assertEqual(headers[b"x-content-type-options"], b"nosniff")
        self.assertEqual(headers[b"x-frame-options"], b"DENY")
        self.assertIn(b"strict-transport-security", headers)

    @staticmethod
    async def _call_asgi(app, scope):
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        await app(scope, receive, send)
        return messages


if __name__ == "__main__":
    unittest.main()
