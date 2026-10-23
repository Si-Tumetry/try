from collections.abc import Iterable

from core.actor import Actor
from core.errors import NotFound, PermissionDenied

CANDIDATE_VIEWER_ROLES = frozenset({"employer", "business", "admin"})
OPPORTUNITY_ROLES = frozenset({"youth", "admin"})


def require_scope(actor: Actor, scope: str) -> None:
    if scope not in actor.scopes:
        raise PermissionDenied(f"missing scope: {scope}")


def require_role(actor: Actor, roles: Iterable[str]) -> None:
    if actor.role not in set(roles):
        raise PermissionDenied("this operation is not allowed for your account type")


def require_owner_or_admin(actor: Actor, owner_user_id: str) -> None:
    """Returns NotFound rather than Forbidden so ownership of a record is not revealed."""
    if actor.role == "admin":
        return
    if actor.user_id is None or actor.user_id != owner_user_id:
        raise NotFound("not found")
