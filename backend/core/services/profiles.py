from collections.abc import Callable
from dataclasses import replace
from typing import Any, TypeVar
from uuid import uuid4

from core.actor import Actor
from core.config import AVAILABILITY_RANK, SUPPORTED_COUNTRIES
from core.cv.extract import extract_text
from core.cv.skills import profile_skills_from_cv
from core.domain import Candidate, Skill
from core.errors import NotFound, PermissionDenied, ValidationFailed, YppError
from core.ports import AuditSink, Store
from core.services.audit import record, result_for
from core.services.permissions import require_role, require_scope

T = TypeVar("T")

YOUTH_SCOPES = frozenset({"read:public", "write:own_profile"})


class ProfileService:
    """A youth member's own profile, built from a CV. Only the owner can read or change it."""

    def __init__(self, *, store: Store, audit: AuditSink) -> None:
        self._store = store
        self._audit = audit

    def create_profile(
        self,
        actor: Actor,
        *,
        cv_filename: str,
        cv_bytes: bytes,
        country: str,
        availability: str | None,
        searchable: bool,
        consent: bool,
    ) -> dict[str, Any]:
        args = {"country": country, "availability": availability, "searchable": searchable, "cv_type": _kind(cv_filename)}
        return self._audited(actor, "create_profile", args, lambda: self._create(
            actor, cv_filename, cv_bytes, country, availability, searchable, consent))

    def get_profile(self, actor: Actor) -> dict[str, Any]:
        return self._audited(actor, "get_profile", {}, lambda: _view(self._own(actor), self._taxonomy()))

    def update_profile(
        self,
        actor: Actor,
        *,
        country: str,
        availability: str | None,
        searchable: bool,
        cv_filename: str | None = None,
        cv_bytes: bytes | None = None,
    ) -> dict[str, Any]:
        args = {"country": country, "availability": availability, "searchable": searchable,
                "cv_type": _kind(cv_filename) if cv_filename else None}
        return self._audited(actor, "update_profile", args, lambda: self._update(
            actor, country, availability, searchable, cv_filename, cv_bytes))

    def delete_profile(self, actor: Actor) -> None:
        self._audited(actor, "delete_profile", {}, lambda: self._delete(actor))

    def profile_id_for(self, actor: Actor) -> str:
        return self._own(actor).profile_id

    def _create(self, actor, cv_filename, cv_bytes, country, availability, searchable, consent) -> dict[str, Any]:
        _require_youth(actor)
        if not consent:
            raise ValidationFailed("you must agree to NextStep reading your CV to match you with opportunities")
        _check_country(country)
        _check_availability(availability)
        if self._store.candidate_for_owner(actor.user_id):
            raise ValidationFailed("this account already has a profile. Update it instead")
        skills = self._skills_from_cv(cv_filename, cv_bytes)
        cand = Candidate(
            profile_id=str(uuid4()),
            owner_user_id=actor.user_id,
            country=country,
            status="active",
            searchable=searchable,
            availability=availability,
            skills=skills,
        )
        self._store.put_candidate(cand)
        return _view(cand, self._taxonomy())

    def _update(self, actor, country, availability, searchable, cv_filename, cv_bytes) -> dict[str, Any]:
        _require_youth(actor)
        _check_country(country)
        _check_availability(availability)
        cand = self._own(actor)
        skills = cand.skills
        if cv_bytes is not None:
            skills = self._skills_from_cv(cv_filename or "", cv_bytes)
        updated = replace(
            cand, country=country, availability=availability, searchable=searchable, skills=skills
        )
        self._store.put_candidate(updated)
        return _view(updated, self._taxonomy())

    def _delete(self, actor) -> None:
        _require_youth(actor)
        cand = self._own(actor)
        self._store.put_candidate(replace(cand, deleted=True, searchable=False, skills={}))

    def _skills_from_cv(self, filename: str, data: bytes) -> dict[str, Any]:
        text = extract_text(filename, data)
        skills = profile_skills_from_cv(text, self._taxonomy().values())
        if not skills:
            raise ValidationFailed(
                "we did not find any skills we recognise in this CV. Add the tools, subjects or "
                "practical skills you use, then upload it again"
            )
        return skills

    def _own(self, actor: Actor) -> Candidate:
        _require_youth(actor)
        cand = self._store.candidate_for_owner(actor.user_id)
        if cand is None:
            raise NotFound("you do not have a profile yet")
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


def _require_youth(actor: Actor) -> None:
    require_role(actor, {"youth"})
    require_scope(actor, "write:own_profile")
    if actor.user_id is None:
        raise PermissionDenied("sign in to manage a profile")


def _check_country(country: str) -> None:
    if country not in SUPPORTED_COUNTRIES:
        raise ValidationFailed(f"country must be one of {sorted(SUPPORTED_COUNTRIES)}")


def _check_availability(availability: str | None) -> None:
    if availability is not None and availability not in AVAILABILITY_RANK:
        raise ValidationFailed(f"availability must be one of {sorted(AVAILABILITY_RANK)}")


def _kind(filename: str | None) -> str:
    return (filename or "").rsplit(".", 1)[-1].lower() if filename and "." in filename else "unknown"


def _view(cand: Candidate, taxonomy: dict[str, Skill]) -> dict[str, Any]:
    skills = [
        {
            "skill_id": ps.skill_id,
            "name": taxonomy[ps.skill_id].name if ps.skill_id in taxonomy else ps.skill_id,
            "level": ps.level,
        }
        for ps in cand.skills.values()
    ]
    skills.sort(key=lambda s: s["name"].lower())
    return {
        "profile_id": cand.profile_id,
        "country": cand.country,
        "availability": cand.availability,
        "searchable": cand.searchable,
        "skills": skills,
    }
