import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from core.actor import Actor
from core.errors import NotFound, PermissionDenied, ValidationFailed
from core.ports import AuditEvent, AuditSink


def hash_args(args: dict[str, Any]) -> str:
    canonical = json.dumps(args, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def result_for(exc: Exception) -> str:
    if isinstance(exc, PermissionDenied):
        return "denied"
    if isinstance(exc, NotFound):
        return "not_found"
    if isinstance(exc, ValidationFailed):
        return "error"
    return "error"


def record(sink: AuditSink, actor: Actor, operation: str, args: dict[str, Any], result: str) -> None:
    sink.write(
        AuditEvent(
            actor_id=actor.user_id,
            actor_role=actor.role,
            door=actor.door,
            operation=operation,
            args_hash=hash_args(args),
            result=result,
            request_id=actor.request_id,
            created_at=datetime.now(timezone.utc),
        )
    )


class InMemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)
