import json
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

from core.domain import Listing, Skill
from core.errors import YppError
from core.ingestion.listing_skills import skills_for_listing
from core.ports import Embedder

DEMO_ENVIRONMENTS = frozenset({"dev", "demo"})


class EnvironmentGuard(YppError):
    code = "forbidden"


def check_environment(app_env: str) -> None:
    """Demo listings never load in production. TECHNICAL.md §14.17."""
    if app_env not in DEMO_ENVIRONMENTS:
        raise EnvironmentGuard(f"demo data may only load in {sorted(DEMO_ENVIRONMENTS)}, not {app_env!r}")


def _listing_type(title: str) -> str:
    lowered = title.lower()
    if "intern" in lowered:
        return "internship"
    if "apprentice" in lowered:
        return "apprenticeship"
    return "job"


def listing_from_record(
    rec: dict[str, Any],
    *,
    approve_for_demo: bool,
    embedder: Embedder | None = None,
    taxonomy: Iterable[Skill] = (),
) -> Listing:
    countries = tuple(rec.get("eligible_countries") or ())
    needs_review = rec.get("status") == "needs_review" or bool(rec.get("unmapped_locations"))
    if approve_for_demo and not needs_review:
        status = "active"
    else:
        status = "pending_review"
    description = rec.get("description") or ""
    embedding = None
    if embedder is not None:
        embedding = tuple(embedder.embed(f"{rec['title']}\n{description}"))
    skills = skills_for_listing(rec["title"], description, taxonomy)
    return Listing(
        listing_id=f"{rec['source_key']}:{rec['external_id']}",
        owner_user_id=f"ingest:{rec['source_key']}",
        type=_listing_type(rec["title"]),
        title=rec["title"],
        description=description,
        country=countries[0] if countries else None,
        status=status,
        location_text=rec.get("location_text") or "",
        eligible_countries=countries,
        work_mode=rec.get("work_mode") or "unspecified",
        scope=rec.get("scope") or "unspecified",
        needs_review=needs_review,
        source_key=rec["source_key"],
        external_id=rec["external_id"],
        source_url=rec.get("source_url"),
        employer_name=rec.get("employer_name"),
        expires_at=_date_or_none(rec.get("expires_at")),
        demo=True,
        embedding=embedding,
        skills=skills,
    )


def _date_or_none(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def load_snapshot(
    path: Path,
    *,
    app_env: str,
    embedder: Embedder | None = None,
    taxonomy: Iterable[Skill] = (),
) -> list[Listing]:
    check_environment(app_env)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    approve = app_env in DEMO_ENVIRONMENTS
    taxonomy = list(taxonomy)
    listings = []
    for rec in data["listings"]:
        if rec.get("status") == "rejected":
            continue
        listings.append(
            listing_from_record(rec, approve_for_demo=approve, embedder=embedder, taxonomy=taxonomy)
        )
    return listings
