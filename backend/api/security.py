from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

PRIVATE_PREFIXES = ("/v1/me/", "/v1/profiles")


class SecurityHeaders:
    """Adds defensive headers to every API response. The API returns JSON only, so nothing may render it as a page."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        private = scope["path"].startswith(PRIVATE_PREFIXES)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("Referrer-Policy", "no-referrer")
                headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
                headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
                if private:
                    headers["Cache-Control"] = "no-store"
            await send(message)

        await self.app(scope, receive, send_with_headers)
