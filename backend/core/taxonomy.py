import json
import re
import uuid
from pathlib import Path

from core.domain import Skill
from core.errors import YppError

TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "taxonomy" / "skills.json"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
MIN_ALIAS_CHARS = 3
# Common words that would match ordinary job-posting text. They are never allowed as names or aliases.
BLOCKED_TERMS = frozenset(
    {
        "the", "and", "for", "with", "work", "team", "help", "good", "great", "best", "new", "use",
        "key", "lead", "role", "job", "skill", "skills", "experience", "knowledge", "support", "general",
        "office", "service", "services", "data", "design", "management", "analysis", "planning",
        "hiring", "supervision", "filing", "sourcing", "forecasting", "layers", "logistics",
    }
)
_NAMESPACE = uuid.UUID("6f1c2a52-9d7e-4f0a-8e3b-5b2d1c0a9e11")


class TaxonomyError(YppError):
    code = "internal_error"


def _normalise(text: str) -> str:
    return " ".join(text.lower().split())


def load_taxonomy(path: Path = TAXONOMY_PATH) -> list[Skill]:
    """Loads and validates the canonical taxonomy. Any problem stops the load with a clear message."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not data.get("version"):
        raise TaxonomyError("taxonomy file has no version")
    skills: list[Skill] = []
    seen_slugs: set[str] = set()
    seen_terms: dict[str, str] = {}

    def claim(term: str, slug: str, *, is_alias: bool) -> None:
        key = _normalise(term)
        if is_alias:
            if len(key) < MIN_ALIAS_CHARS:
                raise TaxonomyError(f"{slug}: alias {term!r} is shorter than {MIN_ALIAS_CHARS} characters")
            if key in BLOCKED_TERMS:
                raise TaxonomyError(f"{slug}: alias {term!r} is a common word and would match job text")
        if key in seen_terms and seen_terms[key] != slug:
            raise TaxonomyError(f"{slug}: term {term!r} already belongs to {seen_terms[key]}")
        seen_terms[key] = slug

    for entry in data["skills"]:
        slug = entry.get("slug", "")
        if not SLUG.match(slug):
            raise TaxonomyError(f"invalid slug {slug!r}")
        if slug in seen_slugs:
            raise TaxonomyError(f"duplicate slug {slug!r}")
        seen_slugs.add(slug)
        name = entry.get("name", "").strip()
        path_parts = tuple(entry.get("path") or ())
        if not name or len(name) > 80:
            raise TaxonomyError(f"{slug}: name must be 1 to 80 characters")
        if not path_parts or not all(isinstance(p, str) and p.strip() for p in path_parts):
            raise TaxonomyError(f"{slug}: path must be a non-empty list of names")
        aliases = tuple(entry.get("aliases") or ())
        claim(name, slug, is_alias=False)
        for alias in aliases:
            claim(alias, slug, is_alias=True)
        skills.append(
            Skill(
                skill_id=str(uuid.uuid5(_NAMESPACE, slug)),
                slug=slug,
                name=name,
                category=path_parts[0],
                taxonomy_path=path_parts,
                aliases=tuple(aliases),
                suggested_projects=tuple(entry.get("suggested_projects") or ()),
            )
        )
    return sorted(skills, key=lambda s: s.slug)
