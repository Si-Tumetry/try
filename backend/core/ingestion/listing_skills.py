from collections.abc import Iterable

from core.config import SearchConfig
from core.domain import Skill, SkillReq
from core.text import skill_mentions


def skills_for_listing(
    title: str,
    description: str,
    taxonomy: Iterable[Skill],
    cfg: SearchConfig = SearchConfig(),
) -> tuple[SkillReq, ...]:
    """Deterministic step of listing skill extraction: canonical names and aliases only.

    A skill named in the title is a must-have at the default must level. A skill named only
    in the description is nice-to-have at the default nice level. Matches are whole-word, so
    "java" does not match "javascript". LLM extraction for phrasing the taxonomy does not
    list will come later and go through the review queue (TECHNICAL.md section 4.3).
    """
    skills = list(taxonomy)
    in_title = {s.skill_id for s in skill_mentions(title, skills)}
    everywhere = {s.skill_id for s in skill_mentions(f"{title}\n{description}", skills)}
    reqs = []
    for skill in sorted(everywhere, key=lambda sid: next(s.slug for s in skills if s.skill_id == sid)):
        if skill in in_title:
            reqs.append(SkillReq(skill, cfg.default_must_level, True))
        else:
            reqs.append(SkillReq(skill, cfg.default_nice_level, False))
    return tuple(reqs)
