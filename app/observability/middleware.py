import time
import uuid

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.observability.logging import (
    bind_request_context,
    clear_request_context,
    get_logger,
)

log = get_logger(__name__)

_SKIP_PATHS = frozenset({"/health", "/health/live", "/health/ready", "/metrics"})


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        request_id = (
            headers.get(b"x-request-id", b"").decode()
            or headers.get(b"x-correlation-id", b"").decode()
            or str(uuid.uuid4())
        )

        scope["state"] = getattr(scope.get("app"), "state", None) or {}
        bind_request_context(request_id=request_id)

        async def send_with_header(message):
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers", []))
                raw_headers.append((b"x-request-id", request_id.encode()))
                raw_headers.append((b"x-correlation-id", request_id.encode()))
                message = {**message, "headers": raw_headers}
            await send(message)

        await self.app(scope, receive, send_with_header)


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in _SKIP_PATHS:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        start = time.perf_counter()

        bind_request_context(
            http_method=request.method,
            http_path=path,
            client_ip=_get_client_ip(scope),
        )

        log.info("request.started")

        status_code = 500

        async def wrapped_send(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception:
            log.exception("request.unhandled_exception")
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            log.info(
                "request.finished", status_code=status_code, duration_ms=duration_ms
            )
            clear_request_context()


def register_middleware(app) -> None:
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)


def _get_client_ip(scope: Scope) -> str:
    headers = dict(scope.get("headers", []))
    forwarded = headers.get(b"x-forwarded-for", b"").decode()
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"
