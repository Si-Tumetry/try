from collections.abc import Iterable

from core.config import SUPPORTED_COUNTRIES, SearchConfig
from core.domain import Listing, Requirement, Skill, SkillReq
from core.errors import ValidationFailed
from core.text import skill_mentions


def _index(skills: Iterable[Skill]) -> dict[str, Skill]:
    index: dict[str, Skill] = {}
    for skill in skills:
        index.setdefault(skill.name.lower(), skill)
    for skill in skills:
        for alias in skill.aliases:
            index.setdefault(alias.lower(), skill)
    return index


def parse_requirement(
    query: str,
    skill_params: list[str] | None,
    *,
    country: str | None,
    skills: list[Skill],
    cfg: SearchConfig,
) -> tuple[Requirement, tuple[str, ...]]:
    """v1 parser: explicit `skills` become must-have, skills named in the query become nice-to-have.

    TECHNICAL.md §5.1 specifies an LLM parser for free text. This deterministic version
    is the fallback the design allows when parsing fails.
    """
    query = (query or "").strip()
    if len(query) > cfg.max_query_chars:
        raise ValidationFailed(f"query must be at most {cfg.max_query_chars} characters")

    params = list(skill_params or [])
    if len(params) > cfg.max_skills_param:
        raise ValidationFailed(f"at most {cfg.max_skills_param} skills are allowed")

    if country is not None:
        country = country.strip().upper()
        if country not in SUPPORTED_COUNTRIES:
            raise ValidationFailed("country must be one of NG, ZA, KE, GH")

    index = _index(skills)
    must: dict[str, SkillReq] = {}
    unknown: list[str] = []
    for raw in params:
        name, sep, level_text = raw.partition(":")
        skill = index.get(name.strip().lower())
        if skill is None:
            unknown.append(raw)
            continue
        level = cfg.default_must_level
        if sep:
            try:
                level = int(level_text.strip())
            except ValueError as exc:
                raise ValidationFailed("skill level must be a whole number from 1 to 5") from exc
            if not 1 <= level <= 5:
                raise ValidationFailed("skill level must be from 1 to 5")
        must[skill.skill_id] = SkillReq(skill.skill_id, level, True)

    nice: dict[str, SkillReq] = {}
    for skill in skill_mentions(query, skills):
        if skill.skill_id in must:
            continue
        nice[skill.skill_id] = SkillReq(skill.skill_id, cfg.default_nice_level, False)

    if not query and not must:
        raise ValidationFailed("provide a query or at least one recognised skill")

    requirement = Requirement(
        text=query,
        skills=(*must.values(), *nice.values()),
        country=country,
    )
    return requirement, tuple(unknown)


def listing_requirement(listing: Listing) -> Requirement:
    return Requirement(
        text=f"{listing.title}\n{listing.description}",
        skills=listing.skills,
        country=listing.country,
        location_city=listing.location_city,
        location_region=listing.location_region,
        pay_min=listing.pay_min,
        pay_max=listing.pay_max,
    )
