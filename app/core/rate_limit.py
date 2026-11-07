import math
import time
from collections import deque
from typing import Hashable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SlidingWindowLimiter:
    def __init__(self, max_keys: int = 20_000) -> None:
        self._windows: dict[tuple[Hashable, ...], deque[float]] = {}
        self._max_keys = max_keys

    def _prune(
        self, key: tuple[Hashable, ...], window_seconds: int, now: float
    ) -> deque[float]:
        attempts = self._windows.get(key)
        if attempts is None:
            return deque()
        while attempts and now - attempts[0] >= window_seconds:
            attempts.popleft()
        if not attempts:
            del self._windows[key]
            return deque()
        return attempts

    def retry_after(
        self,
        key: tuple[Hashable, ...],
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> int | None:
        current_time = time.monotonic() if now is None else now
        attempts = self._prune(key, window_seconds, current_time)
        if len(attempts) < limit:
            return None
        return max(1, math.ceil(window_seconds - (current_time - attempts[0])))

    def record(
        self,
        key: tuple[Hashable, ...],
        window_seconds: int,
        now: float | None = None,
    ) -> None:
        current_time = time.monotonic() if now is None else now
        attempts = self._prune(key, window_seconds, current_time)
        if key not in self._windows and len(self._windows) >= self._max_keys:
            self._windows.pop(next(iter(self._windows)))
        if key not in self._windows:
            self._windows[key] = attempts
        attempts.append(current_time)

    def clear(self, key: tuple[Hashable, ...]) -> None:
        self._windows.pop(key, None)

    def consume(
        self,
        key: tuple[Hashable, ...],
        limit: int,
        window_seconds: int,
    ) -> int | None:
        retry_after = self.retry_after(key, limit, window_seconds)
        if retry_after is not None:
            return retry_after
        self.record(key, window_seconds)
        return None


request_limiter = SlidingWindowLimiter()
login_failure_limiter = SlidingWindowLimiter()


def _login_keys(client_ip: str, username: str) -> tuple[tuple[Hashable, ...], ...]:
    normalized_username = username.strip().casefold()[:100]
    return (
        ("login-user-ip", client_ip, normalized_username),
        ("login-ip", client_ip),
    )


def login_lockout_retry_after(
    client_ip: str, username: str, failure_limit: int, lockout_seconds: int
) -> int | None:
    user_key, ip_key = _login_keys(client_ip, username)
    return (
        login_failure_limiter.retry_after(user_key, failure_limit, lockout_seconds)
        or login_failure_limiter.retry_after(
            ip_key, failure_limit * 6, lockout_seconds
        )
    )


def record_login_failure(
    client_ip: str,
    username: str,
    failure_limit: int,
    lockout_seconds: int,
) -> int | None:
    keys = _login_keys(client_ip, username)
    for key in keys:
        login_failure_limiter.record(key, lockout_seconds)
    return login_lockout_retry_after(
        client_ip, username, failure_limit, lockout_seconds
    )


def clear_login_failures(client_ip: str, username: str) -> None:
    user_key, _ = _login_keys(client_ip, username)
    login_failure_limiter.clear(user_key)


class APIRateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        requests: int,
        window_seconds: int,
    ) -> None:
        self.app = app
        self.requests = requests
        self.window_seconds = window_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] == "http"
            and scope["method"] != "OPTIONS"
            and scope["path"].startswith("/api/v1")
        ):
            client = scope.get("client")
            client_ip = client[0] if client else "unknown"
            retry_after = request_limiter.consume(
                ("api", client_ip), self.requests, self.window_seconds
            )
            if retry_after is not None:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "طلبات كثيرة، حاول مرة أخرى لاحقاً"},
                    headers={"Retry-After": str(retry_after)},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, production: bool) -> None:
        self.app = app
        self.production = production

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"no-referrer"),
                        (
                            b"permissions-policy",
                            b"camera=(), microphone=(), geolocation=()",
                        ),
                    ]
                )
                if self.production and scope.get("scheme") == "https":
                    headers.append(
                        (
                            b"strict-transport-security",
                            b"max-age=31536000; includeSubDomains",
                        )
                    )
            await send(message)

        await self.app(scope, receive, send_with_security_headers)
