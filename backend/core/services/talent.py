from collections.abc import Callable
from datetime import date
from typing import Any, TypeVar

from core.actor import Actor
from core.config import SUPPORTED_COUNTRIES, SearchConfig
from core.domain import Candidate, Listing, Requirement, Skill
from core.engine.explain import candidate_view, matched_and_missing, projects_for, skill_rows
from core.engine.filters import passes_candidate_filters, passes_listing_filters
from core.engine.parser import listing_requirement, parse_requirement
from core.engine.rag import Scored, embed_query, run_talent_search, score_against
from core.errors import NotFound, ValidationFailed, YppError
from core.ports import LLM, AuditSink, Embedder, Store
from core.services.audit import record, result_for
from core.services.permissions import (
    CANDIDATE_VIEWER_ROLES,
    OPPORTUNITY_ROLES,
    require_owner_or_admin,
    require_role,
    require_scope,
)

T = TypeVar("T")


class TalentService:
    """The single service layer. REST and MCP call these methods and nothing else."""

    def __init__(
        self,
        *,
        store: Store,
        audit: AuditSink,
        embedder: Embedder | None = None,
        llm: LLM | None = None,
        cfg: SearchConfig = SearchConfig(),
        clock: Callable[[], date] = date.today,
    ) -> None:
        self._store = store
        self._audit = audit
        self._embedder = embedder
        self._llm = llm
        self._cfg = cfg
        self._clock = clock

    def search_talent(
        self,
        actor: Actor,
        query: str = "",
        *,
        skills: list[str] | None = None,
        country: str | None = None,
        min_score: int | None = None,
        limit: int = 10,
        rerank: bool = True,
    ) -> dict[str, Any]:
        args = {"query": query, "skills": skills, "country": country, "min_score": min_score, "limit": limit, "rerank": rerank}
        return self._audited(actor, "search_talent", args, lambda: self._search_talent(
            actor, query, skills, country, min_score, limit, rerank))

    def score_candidate(
        self,
        actor: Actor,
        profile_id: str,
        *,
        query: str = "",
        skills: list[str] | None = None,
        country: str | None = None,
    ) -> dict[str, Any]:
        args = {"profile_id": profile_id, "query": query, "skills": skills, "country": country}
        return self._audited(actor, "score_candidate", args, lambda: self._score_candidate(
            actor, profile_id, query, skills, country))

    def get_profile(self, actor: Actor, profile_id: str) -> dict[str, Any]:
        args = {"profile_id": profile_id}
        return self._audited(actor, "get_profile", args, lambda: self._get_profile(actor, profile_id))

    def search_opportunities(
        self,
        actor: Actor,
        profile_id: str,
        *,
        country: str | None = None,
        min_score: int | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        args = {"profile_id": profile_id, "country": country, "min_score": min_score, "limit": limit}
        return self._audited(actor, "search_opportunities", args, lambda: self._search_opportunities(
            actor, profile_id, country, min_score, limit))

    def get_skill_gap(self, actor: Actor, listing_id: str, profile_id: str) -> dict[str, Any]:
        args = {"listing_id": listing_id, "profile_id": profile_id}
        return self._audited(actor, "get_skill_gap", args, lambda: self._get_skill_gap(
            actor, listing_id, profile_id))

    def list_skills(
        self,
        actor: Actor,
        *,
        query: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        args = {"query": query, "category": category, "limit": limit}
        return self._audited(actor, "list_skills", args, lambda: self._list_skills(
            actor, query, category, limit))

    def _search_talent(self, actor, query, skills, country, min_score, limit, rerank):
        require_scope(actor, "read:candidates")
        require_role(actor, CANDIDATE_VIEWER_ROLES)
        _check_limit(limit, self._cfg)
        threshold = self._cfg.default_min_score if min_score is None else min_score
        _check_range(threshold, 0, 100, "min_score")

        req, unknown = parse_requirement(
            query, skills, country=country, skills=self._store.skills(), cfg=self._cfg
        )
        outcome = run_talent_search(
            req,
            store=self._store,
            embedder=self._embedder,
            llm=self._llm,
            as_of=self._clock(),
            cfg=self._cfg,
            rerank=rerank,
            min_score=threshold,
        )
        taxonomy = self._taxonomy()
        page = outcome.ranked[:limit]
        return {
            "results": [
                candidate_view(s, req, taxonomy, visible=s.candidate.employer_fields) for s in page
            ],
            "total_matching": len(outcome.ranked),
            "truncated": len(outcome.ranked) > limit,
            "requirement": _requirement_summary(req, taxonomy),
            "unknown_skills": list(unknown),
            "retrieval_channels": list(outcome.channels),
            "embedding_status": outcome.embedding_status,
            "rerank_status": outcome.rerank_status,
            "pool_size": outcome.pool_size,
        }

    def _score_candidate(self, actor, profile_id, query, skills, country):
        require_scope(actor, "read:candidates")
        require_role(actor, CANDIDATE_VIEWER_ROLES)
        cand = self._searchable_candidate(profile_id)
        req, unknown = parse_requirement(
            query, skills, country=country, skills=self._store.skills(), cfg=self._cfg
        )
        req_vec, embedding_status = embed_query(self._embedder, req.text)
        scored = _single(req, cand, req_vec, self._clock(), self._cfg)
        taxonomy = self._taxonomy()
        return {
            "result": candidate_view(scored, req, taxonomy, visible=cand.employer_fields),
            "unknown_skills": list(unknown),
            "embedding_status": embedding_status,
        }

    def _get_profile(self, actor, profile_id):
        require_scope(actor, "read:public")
        cand = self._store.get_candidate(profile_id)
        if (
            cand is None
            or cand.deleted
            or cand.suspended
            or cand.status != "active"
            or not cand.public_fields
        ):
            raise NotFound("profile not found")
        vis = cand.public_fields
        taxonomy = self._taxonomy()
        text = {}
        if "headline" in vis:
            text["headline"] = cand.headline
        if "bio" in vis:
            text["bio"] = cand.bio
        return {
            "profile_id": cand.profile_id,
            "untrusted": True,
            "untrusted_text": text,
            "country": cand.country if "location" in vis else None,
            "availability": cand.availability if "availability" in vis else None,
            "languages": sorted(cand.languages) if "languages" in vis else None,
            "skills": [
                {"name": taxonomy[sid].name if sid in taxonomy else sid, "level": ps.level}
                for sid, ps in sorted(cand.skills.items())
            ] if "skills" in vis else None,
            "evidence": [
                {"type": ev.type, "title": ev.title, "url": ev.url}
                for ev in cand.evidence
                if ev.verified and "evidence" in vis
            ],
        }

    def _search_opportunities(self, actor, profile_id, country, min_score, limit):
        require_scope(actor, "read:public")
        require_role(actor, OPPORTUNITY_ROLES)
        _check_limit(limit, self._cfg)
        threshold = self._cfg.default_min_score if min_score is None else min_score
        _check_range(threshold, 0, 100, "min_score")
        if country is not None:
            country = country.strip().upper()
            if country not in SUPPORTED_COUNTRIES:
                raise ValidationFailed("country must be one of NG, ZA, KE, GH")

        cand = self._owned_active_candidate(actor, profile_id)
        target = country or cand.country
        as_of = self._clock()
        taxonomy = self._taxonomy()

        scored_listings: list[tuple[float, Listing, Any]] = []
        for listing in self._store.listings():
            if not passes_listing_filters(listing, target):
                continue
            req = listing_requirement(listing)
            result = score_against(req, cand, req_vector=listing.embedding, as_of=as_of, cfg=self._cfg)
            if result.score >= threshold:
                scored_listings.append((result.score, listing, result))
        scored_listings.sort(key=lambda t: (-t[0], t[1].listing_id))

        page = scored_listings[:limit]
        results = []
        for _, listing, result in page:
            req = listing_requirement(listing)
            rows = skill_rows(req, cand, taxonomy)
            matched, missing = matched_and_missing(rows)
            results.append(
                {
                    "listing_id": listing.listing_id,
                    "title": listing.title,
                    "type": listing.type,
                    "country": listing.country,
                    "score": result.score,
                    "band": result.band,
                    "confidence": {"value": round(result.confidence, 2), "label": result.confidence_label},
                    "matched_skills": matched,
                    "missing_skills": missing,
                    "next_project": (projects_for(missing, taxonomy) or [None])[0],
                }
            )
        return {
            "results": results,
            "total_matching": len(scored_listings),
            "truncated": len(scored_listings) > limit,
        }

    def _get_skill_gap(self, actor, listing_id, profile_id):
        require_scope(actor, "read:public")
        cand = self._owned_active_candidate(actor, profile_id)
        listing = self._store.get_listing(listing_id)
        if listing is None or listing.deleted or listing.status != "active":
            raise NotFound("listing not found")
        req = listing_requirement(listing)
        as_of = self._clock()
        result = score_against(req, cand, req_vector=listing.embedding, as_of=as_of, cfg=self._cfg)
        taxonomy = self._taxonomy()
        rows = skill_rows(req, cand, taxonomy)
        matched, missing = matched_and_missing(rows)
        return {
            "listing_id": listing.listing_id,
            "score": result.score,
            "band": result.band,
            "matched_skills": matched,
            "missing_skills": missing,
            "projects": projects_for(missing, taxonomy),
        }

    def _list_skills(self, actor, query, category, limit):
        require_scope(actor, "read:public")
        if not 1 <= limit <= 100:
            raise ValidationFailed("limit must be from 1 to 100")
        skills = self._store.skills()
        if category:
            skills = [s for s in skills if s.category.lower() == category.strip().lower()]
        if query:
            q = query.strip().lower()
            skills = [
                s for s in skills
                if q in s.name.lower() or any(q in a.lower() for a in s.aliases)
            ]
        skills.sort(key=lambda s: s.name.lower())
        page = skills[:limit]
        return {
            "skills": [
                {
                    "skill_id": s.skill_id,
                    "slug": s.slug,
                    "name": s.name,
                    "category": s.category,
                    "taxonomy_path": list(s.taxonomy_path),
                }
                for s in page
            ],
            "total_matching": len(skills),
            "truncated": len(skills) > limit,
        }

    def _searchable_candidate(self, profile_id: str) -> Candidate:
        cand = self._store.get_candidate(profile_id)
        if cand is None or not passes_candidate_filters(cand, Requirement()):
            raise NotFound("profile not found")
        return cand

    def _owned_active_candidate(self, actor: Actor, profile_id: str) -> Candidate:
        cand = self._store.get_candidate(profile_id)
        if cand is None or cand.deleted or cand.suspended or cand.status != "active":
            raise NotFound("profile not found")
        require_owner_or_admin(actor, cand.owner_user_id)
        return cand

    def _taxonomy(self) -> dict[str, Skill]:
        return {s.skill_id: s for s in self._store.skills()}

    def _audited(self, actor: Actor, operation: str, args: dict[str, Any], fn: Callable[[], T]) -> T:
        try:
            out = fn()
        except YppError as exc:
            record(self._audit, actor, operation, args, result_for(exc))
            raise
        except Exception:
            record(self._audit, actor, operation, args, "error")
            raise
        record(self._audit, actor, operation, args, "ok")
        return out


def _single(req: Requirement, cand: Candidate, req_vec, as_of: date, cfg: SearchConfig) -> Scored:
    result = score_against(req, cand, req_vector=req_vec, as_of=as_of, cfg=cfg)
    return Scored(candidate=cand, result=result)


def _requirement_summary(req: Requirement, taxonomy: dict[str, Skill]) -> dict[str, Any]:
    def names(must: bool) -> list[dict[str, Any]]:
        return [
            {"name": taxonomy[sr.skill_id].name if sr.skill_id in taxonomy else sr.skill_id, "level": sr.level}
            for sr in req.skills
            if sr.must == must
        ]

    return {"must_have": names(True), "nice_to_have": names(False), "country": req.country}


def _check_limit(limit: int, cfg: SearchConfig) -> None:
    _check_range(limit, 1, cfg.max_limit, "limit")


def _check_range(value: int, lo: int, hi: int, name: str) -> None:
    if not lo <= value <= hi:
        raise ValidationFailed(f"{name} must be from {lo} to {hi}")
