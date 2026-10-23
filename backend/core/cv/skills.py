from collections.abc import Iterable

from core.domain import ProfileSkill, Skill
from core.text import skill_mention_counts

# A skill named once in a CV is recorded at level 2; named twice or more, at level 3.
# These are the same levels the default requirements use (SearchConfig), so a skill
# named in the CV can meet a requirement without a separate test. Levels are
# self-declared until evidence confirms them, so evidence weight stays low (scoring.py).
LEVEL_ONCE = 2
LEVEL_REPEATED = 3


def profile_skills_from_cv(text: str, taxonomy: Iterable[Skill]) -> dict[str, ProfileSkill]:
    skills = list(taxonomy)
    by_slug = {s.slug: s for s in skills}
    counts = skill_mention_counts(text, skills)
    found: dict[str, ProfileSkill] = {}
    for slug, mentions in counts.items():
        skill = by_slug[slug]
        level = LEVEL_REPEATED if mentions >= 2 else LEVEL_ONCE
        found[skill.skill_id] = ProfileSkill(skill_id=skill.skill_id, level=level)
    return found
