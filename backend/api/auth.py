import hashlib
import secrets
import threading

from core.actor import Actor


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class SessionTokens:
    """Bearer tokens for youth profiles, held in memory and stored only as digests.

    This is a stand-in until real sign-in exists (DESIGN.md §4.6). A token is returned once, when a profile is
    created, and is lost if the browser's storage is cleared or the server restarts.
    """

    def __init__(self) -> None:
        self._actors: dict[str, Actor] = {}
        self._lock = threading.Lock()

    def issue(self, actor: Actor) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._actors[_digest(token)] = actor
        return token

    def resolve(self, token: str) -> Actor | None:
        with self._lock:
            return self._actors.get(_digest(token))

    def revoke(self, token: str) -> None:
        with self._lock:
            self._actors.pop(_digest(token), None)
