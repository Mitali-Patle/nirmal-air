"""Security headers added to every response the app generates."""

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "img-src 'self' data:",
        "connect-src 'self'",
        "form-action 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
    ]
)

BASE_HEADERS: dict[str, str] = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(self), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
}
# Over HTTPS only (production): browsers keep to HTTPS, and any stray http:// link is upgraded.
HTTPS_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "Content-Security-Policy": f"{CONTENT_SECURITY_POLICY}; upgrade-insecure-requests",
}


class SecurityHeadersMiddleware:
    """Pure ASGI middleware that sets security headers without buffering the response."""

    def __init__(self, app: ASGIApp, *, https_only: bool) -> None:
        """Wrap an ASGI app.

        Args:
            app: The application to wrap.
            https_only: Whether the site is served only over HTTPS (production), which adds
                Strict-Transport-Security and upgrades insecure requests.
        """
        self.app = app
        self.headers = BASE_HEADERS | HTTPS_HEADERS if https_only else dict(BASE_HEADERS)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle one ASGI connection, adding headers to HTTP responses."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in self.headers.items():
                    headers.setdefault(name, value)
            await send(message)

        await self.app(scope, receive, send_with_headers)


# The largest real form (a full household) is about 4 KB; anything past this is not a person.
MAX_BODY_BYTES = 16 * 1024
TOO_LARGE_BODY = b"That was too much to send. Please go back and try again."


class BodySizeLimitMiddleware:
    """Pure ASGI middleware that refuses request bodies over a size limit with 413.

    A declared Content-Length is checked before anything is read. A body sent without one is
    read here first, up to the limit, and then handed on, so leaving the header out does not
    get past the limit and the refusal is always a 413.
    """

    def __init__(self, app: ASGIApp, *, max_bytes: int = MAX_BODY_BYTES) -> None:
        """Wrap an ASGI app.

        Args:
            app: The application to wrap.
            max_bytes: The largest body accepted.
        """
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle one ASGI connection, refusing oversized request bodies."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None:
            if not declared.isdigit() or int(declared) > self.max_bytes:
                await _refuse(send)
                return
            await self.app(scope, receive, send)
            return
        messages = await self._read(receive)
        if messages is None:
            await _refuse(send)
            return

        async def replay() -> Message:
            return messages.pop(0) if messages else await receive()

        await self.app(scope, replay, send)

    async def _read(self, receive: Receive) -> list[Message] | None:
        """The body's messages, or None once they pass the limit."""
        messages: list[Message] = []
        received = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] != "http.request":
                return messages
            received += len(message.get("body", b""))
            if received > self.max_bytes:
                return None
            if not message.get("more_body", False):
                return messages


async def _refuse(send: Send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        }
    )
    await send({"type": "http.response.body", "body": TOO_LARGE_BODY})
