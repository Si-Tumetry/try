from dataclasses import dataclass


@dataclass(frozen=True)
class Actor:
    user_id: str | None
    role: str
    scopes: frozenset[str] = frozenset()
    door: str = "mcp"
    request_id: str = ""


ANONYMOUS = Actor(user_id=None, role="anonymous")
