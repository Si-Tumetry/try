from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from core.domain import Candidate, Listing, Skill


class Store(Protocol):
    def skills(self) -> list[Skill]: ...

    def candidates(self) -> list[Candidate]: ...

    def get_candidate(self, profile_id: str) -> Candidate | None: ...

    def candidate_for_owner(self, owner_user_id: str) -> Candidate | None: ...

    def put_candidate(self, cand: Candidate) -> None: ...

    def listings(self) -> list[Listing]: ...

    def get_listing(self, listing_id: str) -> Listing | None: ...


class Embedder(Protocol):
    def embed(self, text: str) -> tuple[float, ...]: ...


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str: ...


@dataclass(frozen=True)
class AuditEvent:
    actor_id: str | None
    actor_role: str
    door: str
    operation: str
    args_hash: str
    result: str
    request_id: str
    created_at: datetime


class AuditSink(Protocol):
    def write(self, event: AuditEvent) -> None: ...
