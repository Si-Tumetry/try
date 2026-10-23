from datetime import date

from core.domain import Candidate, Evidence, Listing, ProfileSkill, Skill, SkillReq
from core.store.memory import InMemoryStore
from tests.fakes import HashingEmbedder

AS_OF = date(2026, 10, 1)

PY = Skill(
    "s-python", "python", "Python", "Technology", ("Technology", "Software", "Languages"),
    aliases=("python3",), suggested_projects=("Build a CLI that cleans a CSV file",),
)
SQL = Skill(
    "s-sql", "sql", "SQL", "Technology", ("Technology", "Data", "Databases"),
    aliases=("postgres", "postgresql"), suggested_projects=("Design a normalised schema for a small shop",),
)
DJANGO = Skill(
    "s-django", "django", "Django", "Technology", ("Technology", "Software", "Frameworks"),
    suggested_projects=("Build a REST endpoint for a booking form",),
)
DATA_ENTRY = Skill(
    "s-data-entry", "data-entry", "Data entry", "Administration", ("Administration", "Records"),
    aliases=("data capture",), suggested_projects=("Digitise 100 paper forms into a spreadsheet",),
)
CUSTOMER = Skill(
    "s-customer-service", "customer-service", "Customer service", "Service", ("Service", "Support"),
    aliases=("customer care",), suggested_projects=("Run a week of mock support tickets",),
)
TAXONOMY = [PY, SQL, DJANGO, DATA_ENTRY, CUSTOMER]

YOUTH_FIELDS = frozenset({"headline", "bio", "skills", "location", "languages", "availability", "evidence"})


def _doc(headline: str, bio: str, skills: dict[str, ProfileSkill], evidence: tuple[Evidence, ...]) -> str:
    names = {s.skill_id: s.name for s in TAXONOMY}
    parts = [headline, bio, " ".join(names[sid] for sid in skills)]
    parts += [ev.title for ev in evidence if ev.verified]
    return " ".join(parts)


def _candidate(embedder, **kw) -> Candidate:
    cand = Candidate(**kw)
    text = _doc(cand.headline, cand.bio, cand.skills, cand.evidence)
    return Candidate(**{**kw, "document_text": text, "embedding": embedder.embed(text)})


def build_candidates(embedder: HashingEmbedder) -> list[Candidate]:
    ada_skills = {
        "s-python": ProfileSkill("s-python", 4, date(2026, 4, 1)),
        "s-sql": ProfileSkill("s-sql", 2, date(2024, 1, 1)),
        "s-django": ProfileSkill("s-django", 2, None),
    }
    ada_evidence = (
        Evidence("project", True, "s-python", "Inventory CLI", "https://github.com/ada/inventory"),
    )
    kojo_skills = {
        "s-data-entry": ProfileSkill("s-data-entry", 4, date(2026, 8, 1)),
        "s-customer-service": ProfileSkill("s-customer-service", 3, date(2025, 5, 1)),
    }
    kojo_evidence = (
        Evidence("certificate", True, "s-customer-service", "Customer care certificate", "https://example.org/cert/123"),
    )
    wanjiru_skills = {
        "s-python": ProfileSkill("s-python", 3, date(2026, 6, 1)),
        "s-sql": ProfileSkill("s-sql", 3, date(2026, 6, 1)),
    }
    wanjiru_evidence = (
        Evidence("assessment", True, "s-python", "Python assessment"),
    )
    def make(**kw):
        return _candidate(embedder, **kw)

    return [
        make(
            profile_id="p-ada", owner_user_id="u-ada", country="NG", status="active", searchable=True,
            headline="Backend developer building Python APIs in Lagos",
            bio="I write python and postgres tools for small shops.",
            availability="now", languages=frozenset({"en"}),
            location_city="Lagos", location_region="Lagos State",
            skills=ada_skills, evidence=ada_evidence,
            employer_fields=YOUTH_FIELDS, public_fields=YOUTH_FIELDS,
        ),
        make(
            profile_id="p-kojo", owner_user_id="u-kojo", country="GH", status="active", searchable=True,
            headline="Data entry clerk in Accra",
            bio="Fast accurate typing and customer care for small firms.",
            availability="within_30_days", languages=frozenset({"en", "tw"}),
            location_city="Accra", location_region="Greater Accra",
            skills=kojo_skills, evidence=kojo_evidence,
            employer_fields=YOUTH_FIELDS, public_fields=YOUTH_FIELDS,
        ),
        make(
            profile_id="p-wanjiru", owner_user_id="u-wanjiru", country="KE", status="active", searchable=True,
            headline="Python and SQL analyst in Nairobi",
            bio="Analyst who ships dashboards.",
            availability="now", languages=frozenset({"en"}),
            location_city="Nairobi", location_region="Nairobi",
            skills=wanjiru_skills, evidence=wanjiru_evidence,
            employer_fields=YOUTH_FIELDS, public_fields=frozenset({"headline"}),
        ),
        make(
            profile_id="p-thandi", owner_user_id="u-thandi", country="ZA", status="active", searchable=False,
            headline="Python developer in Cape Town",
            bio="Senior python and sql engineer.",
            availability="now", languages=frozenset({"en"}),
            skills={"s-python": ProfileSkill("s-python", 5, date(2026, 9, 1)),
                    "s-sql": ProfileSkill("s-sql", 4, date(2026, 9, 1))},
            employer_fields=frozenset(), public_fields=frozenset(),
        ),
        make(
            profile_id="p-deleted", owner_user_id="u-deleted", country="NG", status="active", searchable=True,
            deleted=True, headline="Python engineer", bio="",
            availability="now", skills={"s-python": ProfileSkill("s-python", 5, date(2026, 9, 1))},
            employer_fields=YOUTH_FIELDS, public_fields=YOUTH_FIELDS,
        ),
        make(
            profile_id="p-suspended", owner_user_id="u-suspended", country="NG", status="active", searchable=True,
            suspended=True, headline="Python engineer", bio="",
            availability="now", skills={"s-python": ProfileSkill("s-python", 5, date(2026, 9, 1))},
            employer_fields=YOUTH_FIELDS, public_fields=YOUTH_FIELDS,
        ),
    ]


def build_listings(embedder: HashingEmbedder) -> list[Listing]:
    def listing(**kw):
        text = f"{kw['title']}\n{kw['description']}"
        kw.setdefault("eligible_countries", (kw["country"],))
        kw.setdefault("scope", "in_region")
        return Listing(**kw, embedding=embedder.embed(text))

    return [
        listing(
            listing_id="l-backend", owner_user_id="u-emp1", type="job",
            title="Junior Python developer", description="Build internal tools in python with postgres.",
            country="NG", status="active",
            skills=(SkillReq("s-python", 3, True), SkillReq("s-sql", 2, False)),
            location_city="Lagos", location_region="Lagos State",
        ),
        listing(
            listing_id="l-records", owner_user_id="u-emp2", type="job",
            title="Records clerk", description="Data entry and customer care for a clinic.",
            country="GH", status="active",
            skills=(SkillReq("s-data-entry", 3, True), SkillReq("s-customer-service", 2, False)),
            location_city="Accra", location_region="Greater Accra",
        ),
        listing(
            listing_id="l-paused", owner_user_id="u-emp1", type="job",
            title="Python lead", description="Lead python delivery.",
            country="NG", status="paused",
            skills=(SkillReq("s-python", 4, True),),
        ),
    ]


def build_store(embedder: HashingEmbedder | None = None) -> InMemoryStore:
    embedder = embedder or HashingEmbedder()
    return InMemoryStore(
        skills=TAXONOMY,
        candidates=build_candidates(embedder),
        listings=build_listings(embedder),
    )
