import base64
import json
from collections.abc import Sequence
from typing import TypeVar

from core.errors import ValidationFailed

T = TypeVar("T")


def encode_cursor(offset: int) -> str:
    raw = json.dumps({"o": offset}, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    """Opaque to clients. A malformed or tampered cursor is refused, never trusted blindly."""
    if not cursor:
        return 0
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        offset = data["o"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ValidationFailed("invalid cursor") from exc
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValidationFailed("invalid cursor")
    return offset


def page_of(items: Sequence[T], cursor: str | None, limit: int) -> tuple[list[T], str | None]:
    """Returns (this page, cursor for the next page or None when this is the last page)."""
    offset = decode_cursor(cursor)
    chunk = list(items[offset : offset + limit])
    following = offset + limit
    next_cursor = encode_cursor(following) if following < len(items) else None
    return chunk, next_cursor
