from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Skill:
    skill_id: str
    slug: str
    name: str
    category: str
    taxonomy_path: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    suggested_projects: tuple[str, ...] = ()
    active: bool = True


@dataclass(frozen=True)
class SkillReq:
    skill_id: str
    level: int
    must: bool = True


@dataclass(frozen=True)
class Requirement:
    text: str = ""
    skills: tuple[SkillReq, ...] = ()
    country: str | None = None
    availability: str | None = None
    languages: frozenset[str] = frozenset()
    location_city: str | None = None
    location_region: str | None = None
    pay_min: float | None = None
    pay_max: float | None = None


@dataclass(frozen=True)
class ProfileSkill:
    skill_id: str
    level: int
    last_used: date | None = None


@dataclass(frozen=True)
class Evidence:
    type: str
    verified: bool
    skill_id: str | None = None
    title: str = ""
    url: str | None = None


@dataclass(frozen=True)
class Candidate:
    profile_id: str
    owner_user_id: str
    country: str
    status: str
    searchable: bool
    suspended: bool = False
    deleted: bool = False
    headline: str = ""
    bio: str = ""
    document_text: str = ""
    availability: str | None = None
    languages: frozenset[str] = frozenset()
    location_city: str | None = None
    location_region: str | None = None
    pay_min: float | None = None
    pay_max: float | None = None
    skills: dict[str, ProfileSkill] = field(default_factory=dict)
    evidence: tuple[Evidence, ...] = ()
    public_fields: frozenset[str] = frozenset()
    employer_fields: frozenset[str] = frozenset()
    embedding: tuple[float, ...] | None = None


@dataclass(frozen=True)
class Listing:
    listing_id: str
    owner_user_id: str
    type: str
    title: str
    description: str
    country: str
    status: str
    skills: tuple[SkillReq, ...] = ()
    location_city: str | None = None
    location_region: str | None = None
    pay_min: float | None = None
    pay_max: float | None = None
    deleted: bool = False
    embedding: tuple[float, ...] | None = None
