import hashlib
from typing import Any, Protocol

from starlette.responses import JSONResponse

from core.actor import ANONYMOUS, Actor


class TokenStore(Protocol):
    def resolve(self, token: str) -> Actor | None: ...


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class StaticTokenStore:
    """Development and test store. Production resolves hashed tokens from oauth_tokens (DATABASE.md §4.15)."""

    def __init__(self, tokens: dict[str, Actor]) -> None:
        self._by_digest = {_digest(token): actor for token, actor in tokens.items()}

    def resolve(self, token: str) -> Actor | None:
        return self._by_digest.get(_digest(token))


def _bearer_token(scope: dict[str, Any]) -> str | None:
    for name, value in scope.get("headers", []):
        if name == b"authorization":
            scheme, _, token = value.decode("latin-1").partition(" ")
            if scheme.lower() == "bearer" and token.strip():
                return token.strip()
    return None


class BearerAuthMiddleware:
    def __init__(self, app, tokens: TokenStore) -> None:
        self.app = app
        self.tokens = tokens

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        token = _bearer_token(scope)
        actor = self.tokens.resolve(token) if token else None
        if actor is None:
            response = JSONResponse(
                {"error": {"code": "unauthenticated", "message": "missing or invalid bearer token"}},
                status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="yellowpages"'},
            )
            await response(scope, receive, send)
            return
        scope.setdefault("state", {})["actor"] = actor
        await self.app(scope, receive, send)


def actor_from_context(ctx) -> Actor:
    try:
        request = ctx.request_context.request
    except (AttributeError, ValueError):
        return ANONYMOUS
    if request is None:
        return ANONYMOUS
    return getattr(request.state, "actor", ANONYMOUS)
