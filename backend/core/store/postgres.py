"""The Postgres store (DATABASE.md). Implements the Store protocol used by the service layer.

Reads return the same domain objects as InMemoryStore, so the engine and services do not change.
"""

import uuid
from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Any

from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from core.domain import Candidate, Listing, ProfileSkill, Skill, SkillReq
from core.ports import AuditEvent

# Listing ids are derived from the public listing key, so re-running an import keeps the same row.
LISTING_NAMESPACE = uuid.UUID("3c1f8e2a-6b7d-4c5e-9f10-2a4b6c8d0e12")
INGEST_OWNER_PREFIX = "ingest:"


def listing_row_id(listing_key: str) -> str:
    return str(uuid.uuid5(LISTING_NAMESPACE, listing_key))


class PostgresStore:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool
        self._skills: list[Skill] | None = None

    # ----- reference data ---------------------------------------------------------------

    def skills(self) -> list[Skill]:
        if self._skills is None:
            with self._pool.connection() as conn:
                rows = conn.execute(
                    "SELECT id, slug, name, aliases, taxonomy_path, category, suggested_projects, active "
                    "FROM skills WHERE active ORDER BY slug"
                ).fetchall()
            self._skills = [_skill_from_row(row) for row in rows]
        return list(self._skills)

    def upsert_skills(self, skills: Iterable[Skill], *, retire_missing: bool = True) -> int:
        items = list(skills)
        with self._pool.connection() as conn, conn.transaction():
            for s in items:
                conn.execute(
                    "INSERT INTO skills (id, slug, name, aliases, taxonomy_path, category, suggested_projects, active) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, true) "
                    "ON CONFLICT (id) DO UPDATE SET slug = EXCLUDED.slug, name = EXCLUDED.name, "
                    "aliases = EXCLUDED.aliases, taxonomy_path = EXCLUDED.taxonomy_path, "
                    "category = EXCLUDED.category, suggested_projects = EXCLUDED.suggested_projects, "
                    "active = true, updated_at = now()",
                    (
                        s.skill_id, s.slug, s.name, list(s.aliases), list(s.taxonomy_path), s.category,
                        Jsonb(list(s.suggested_projects)),
                    ),
                )
            if retire_missing:
                conn.execute(
                    "UPDATE skills SET active = false, updated_at = now() WHERE NOT (id = ANY(%s::uuid[]))",
                    ([s.skill_id for s in items],),
                )
        self._skills = None
        return len(items)

    # ----- profiles -----------------------------------------------------------------------

    def candidates(self) -> list[Candidate]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                "SELECT id, user_id, country, availability, status, searchable, deleted_at "
                "FROM profiles WHERE deleted_at IS NULL"
            ).fetchall()
            skills = _profile_skills(conn, None)
        return [_candidate_from_row(row, skills.get(str(row[0]), {})) for row in rows]

    def get_candidate(self, profile_id: str) -> Candidate | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT id, user_id, country, availability, status, searchable, deleted_at "
                "FROM profiles WHERE id = %s",
                (profile_id,),
            ).fetchone()
            if row is None:
                return None
            skills = _profile_skills(conn, profile_id)
        return _candidate_from_row(row, skills.get(profile_id, {}))

    def candidate_for_owner(self, owner_user_id: str) -> Candidate | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT id, user_id, country, availability, status, searchable, deleted_at "
                "FROM profiles WHERE user_id = %s AND deleted_at IS NULL",
                (owner_user_id,),
            ).fetchone()
            if row is None:
                return None
            skills = _profile_skills(conn, str(row[0]))
        return _candidate_from_row(row, skills.get(str(row[0]), {}))

    def put_candidate(self, cand: Candidate) -> None:
        status = "suspended" if cand.suspended else cand.status
        with self._pool.connection() as conn, conn.transaction():
            conn.execute(
                "INSERT INTO profiles (id, user_id, country, availability, status, searchable, deleted_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, CASE WHEN %s THEN now() END) "
                "ON CONFLICT (id) DO UPDATE SET country = EXCLUDED.country, "
                "availability = EXCLUDED.availability, status = EXCLUDED.status, "
                "searchable = EXCLUDED.searchable, deleted_at = EXCLUDED.deleted_at, updated_at = now()",
                (
                    cand.profile_id, cand.owner_user_id, cand.country, cand.availability, status,
                    cand.searchable, cand.deleted,
                ),
            )
            conn.execute("DELETE FROM profile_skills WHERE profile_id = %s", (cand.profile_id,))
            for ps in cand.skills.values():
                conn.execute(
                    "INSERT INTO profile_skills (profile_id, skill_id, level, last_used, source) "
                    "VALUES (%s, %s, %s, %s, 'self')",
                    (cand.profile_id, ps.skill_id, ps.level, ps.last_used),
                )

    # ----- listings -----------------------------------------------------------------------

    def listings(self) -> list[Listing]:
        with self._pool.connection() as conn:
            rows = conn.execute(f"SELECT {_LISTING_COLUMNS} FROM listings WHERE deleted_at IS NULL").fetchall()
            requirements = _listing_requirements(conn, None)
        return [_listing_from_row(row, requirements.get(row[0], ())) for row in rows]

    def get_listing(self, listing_id: str) -> Listing | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                f"SELECT {_LISTING_COLUMNS} FROM listings WHERE listing_key = %s",
                (listing_id,),
            ).fetchone()
            if row is None:
                return None
            requirements = _listing_requirements(conn, listing_id)
        return _listing_from_row(row, requirements.get(row[0], ()))

    def upsert_listings(self, listings: Iterable[Listing]) -> int:
        items = list(listings)
        with self._pool.connection() as conn, conn.transaction():
            for item in items:
                row_id = listing_row_id(item.listing_id)
                owner = None if item.owner_user_id.startswith(INGEST_OWNER_PREFIX) else item.owner_user_id
                conn.execute(
                    "INSERT INTO listings (id, listing_key, owner_user_id, type, title, description, country, "
                    "location_text, location_city, location_region, eligible_countries, unmapped_locations, "
                    "work_mode, scope, status, needs_review, demo, source_key, external_id, source_url, "
                    "employer_name, pay_min, pay_max, expires_at, deleted_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                    "%s, %s, %s, CASE WHEN %s THEN now() END) "
                    "ON CONFLICT (listing_key) DO UPDATE SET owner_user_id = EXCLUDED.owner_user_id, "
                    "type = EXCLUDED.type, title = EXCLUDED.title, description = EXCLUDED.description, "
                    "country = EXCLUDED.country, location_text = EXCLUDED.location_text, "
                    "location_city = EXCLUDED.location_city, location_region = EXCLUDED.location_region, "
                    "eligible_countries = EXCLUDED.eligible_countries, "
                    "unmapped_locations = EXCLUDED.unmapped_locations, work_mode = EXCLUDED.work_mode, "
                    "scope = EXCLUDED.scope, status = EXCLUDED.status, needs_review = EXCLUDED.needs_review, "
                    "demo = EXCLUDED.demo, source_url = EXCLUDED.source_url, employer_name = EXCLUDED.employer_name, "
                    "pay_min = EXCLUDED.pay_min, pay_max = EXCLUDED.pay_max, expires_at = EXCLUDED.expires_at, "
                    "deleted_at = EXCLUDED.deleted_at, updated_at = now()",
                    (
                        row_id, item.listing_id, owner, item.type, item.title, item.description, item.country,
                        item.location_text, item.location_city, item.location_region,
                        list(item.eligible_countries), list(item.unmapped_locations), item.work_mode,
                        item.scope, item.status, item.needs_review, item.demo, item.source_key,
                        item.external_id, item.source_url, item.employer_name,
                        _decimal(item.pay_min), _decimal(item.pay_max), item.expires_at, item.deleted,
                    ),
                )
                conn.execute("DELETE FROM listing_skills WHERE listing_id = %s", (row_id,))
                for sr in item.skills:
                    conn.execute(
                        "INSERT INTO listing_skills (listing_id, skill_id, level, must_have) VALUES (%s, %s, %s, %s)",
                        (row_id, sr.skill_id, sr.level, sr.must),
                    )
        return len(items)

    # ----- audit ----------------------------------------------------------------------------

    def write_audit(self, event: AuditEvent) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                "INSERT INTO audit_log (actor_id, actor_role, door, operation, args_hash, result, request_id, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    event.actor_id, event.actor_role, event.door, event.operation, event.args_hash,
                    event.result, event.request_id, event.created_at,
                ),
            )


class PostgresAuditSink:
    """Audit sink that writes to audit_log. Implements the AuditSink protocol."""

    def __init__(self, store: PostgresStore) -> None:
        self._store = store

    def write(self, event: AuditEvent) -> None:
        self._store.write_audit(event)


_LISTING_COLUMNS = (
    "id, listing_key, owner_user_id, type, title, description, country, location_text, location_city, "
    "location_region, eligible_countries, unmapped_locations, work_mode, scope, status, needs_review, demo, "
    "source_key, external_id, source_url, employer_name, pay_min, pay_max, expires_at, deleted_at"
)


def _skill_from_row(row: tuple[Any, ...]) -> Skill:
    skill_id, slug, name, aliases, path, category, projects, active = row
    return Skill(
        skill_id=str(skill_id),
        slug=slug,
        name=name,
        category=category,
        taxonomy_path=tuple(path),
        aliases=tuple(aliases or ()),
        suggested_projects=tuple(projects or ()),
        active=active,
    )


def _profile_skills(conn, profile_id: str | None) -> dict[str, dict[str, ProfileSkill]]:
    if profile_id is None:
        rows = conn.execute(
            "SELECT ps.profile_id, ps.skill_id, ps.level, ps.last_used FROM profile_skills ps "
            "JOIN profiles p ON p.id = ps.profile_id WHERE p.deleted_at IS NULL"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT profile_id, skill_id, level, last_used FROM profile_skills WHERE profile_id = %s",
            (profile_id,),
        ).fetchall()
    out: dict[str, dict[str, ProfileSkill]] = defaultdict(dict)
    for pid, sid, level, last_used in rows:
        out[str(pid)][str(sid)] = ProfileSkill(skill_id=str(sid), level=level, last_used=last_used)
    return out


def _candidate_from_row(row: tuple[Any, ...], skills: dict[str, ProfileSkill]) -> Candidate:
    profile_id, user_id, country, availability, status, searchable, deleted_at = row
    return Candidate(
        profile_id=str(profile_id),
        owner_user_id=str(user_id),
        country=country,
        status="suspended" if status == "suspended" else status,
        searchable=searchable,
        suspended=status == "suspended",
        deleted=deleted_at is not None,
        availability=availability,
        skills=dict(skills),
    )


def _listing_requirements(conn, listing_key: str | None) -> dict[Any, tuple[SkillReq, ...]]:
    if listing_key is None:
        rows = conn.execute(
            "SELECT ls.listing_id, ls.skill_id, ls.level, ls.must_have FROM listing_skills ls"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT ls.listing_id, ls.skill_id, ls.level, ls.must_have FROM listing_skills ls "
            "JOIN listings l ON l.id = ls.listing_id WHERE l.listing_key = %s",
            (listing_key,),
        ).fetchall()
    out: dict[Any, list[SkillReq]] = defaultdict(list)
    for lid, sid, level, must in rows:
        out[lid].append(SkillReq(skill_id=str(sid), level=level, must=must))
    return {key: tuple(value) for key, value in out.items()}


def _listing_from_row(row: tuple[Any, ...], skills: tuple[SkillReq, ...]) -> Listing:
    (
        row_id, listing_key, owner, type_, title, description, country, location_text, location_city,
        location_region, eligible, unmapped, work_mode, scope, status, needs_review, demo, source_key,
        external_id, source_url, employer_name, pay_min, pay_max, expires_at, deleted_at,
    ) = row
    return Listing(
        listing_id=listing_key,
        owner_user_id=str(owner) if owner else f"{INGEST_OWNER_PREFIX}{source_key}",
        type=type_,
        title=title,
        description=description,
        country=country,
        status=status,
        skills=skills,
        location_city=location_city,
        location_region=location_region,
        pay_min=float(pay_min) if pay_min is not None else None,
        pay_max=float(pay_max) if pay_max is not None else None,
        deleted=deleted_at is not None,
        location_text=location_text or "",
        eligible_countries=tuple(eligible or ()),
        work_mode=work_mode,
        scope=scope,
        needs_review=needs_review,
        source_key=source_key,
        external_id=external_id,
        source_url=source_url,
        employer_name=employer_name,
        expires_at=expires_at if isinstance(expires_at, date) else None,
        demo=demo,
    )


def _decimal(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))
