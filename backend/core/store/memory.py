from collections.abc import Iterable

from core.domain import Candidate, Listing, Skill


class InMemoryStore:
    """Store used by tests and local runs. Production reads Postgres (DATABASE.md)."""

    def __init__(
        self,
        *,
        skills: Iterable[Skill],
        candidates: Iterable[Candidate] = (),
        listings: Iterable[Listing] = (),
    ) -> None:
        self._skills = {s.skill_id: s for s in skills}
        self._candidates = {c.profile_id: c for c in candidates}
        self._listings = {l.listing_id: l for l in listings}

    def skills(self) -> list[Skill]:
        return sorted((s for s in self._skills.values() if s.active), key=lambda s: s.slug)

    def candidates(self) -> list[Candidate]:
        return list(self._candidates.values())

    def get_candidate(self, profile_id: str) -> Candidate | None:
        return self._candidates.get(profile_id)

    def listings(self) -> list[Listing]:
        return list(self._listings.values())

    def get_listing(self, listing_id: str) -> Listing | None:
        return self._listings.get(listing_id)
