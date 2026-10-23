import re
from collections.abc import Iterable

from core.config import SearchConfig
from core.domain import Skill, SkillReq
from core.text import skill_mentions

# Company descriptions name customers and brands, and diversity statements list protected
# characteristics. Neither describes what the job requires, so neither is matched.
_COMPANY_BLOCK = re.compile(
    r"^\s*(about\s+(?!the\s+(role|job|position|team|opportunity)\b|this\s+(role|job|position|opportunity)\b|you\b)"
    r"|who\s+(we\s+are|you\s+are)|our\s+(company|mission|values|culture|story)|why\s+(join|work)\b)",
    re.IGNORECASE,
)
_COMPANY_CLAIMS = re.compile(
    r"world[’']s\s+leading|(over|more\s+than)\s+[\d,]+\s+(\w+\s+){0,2}(brands|customers|clients|companies|partnerships|businesses)\b",
    re.IGNORECASE,
)
_EQUAL_OPPORTUNITY = re.compile(
    r"equal\s+(opportunit|employment)|without\s+regard\s+to|protected\s+characteristic|"
    r"caregiving\s+status|veteran\s+status|gender\s+identity|sexual\s+orientation|"
    r"marital|neurodivergen|genetic\s+information|national\s+origin|disability\s+status|religion",
    re.IGNORECASE,
)


_NON_LATIN = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af\u0600-\u06ff\u0400-\u04ff]")


def is_mostly_non_latin(text: str, threshold: float = 0.05) -> bool:
    """The taxonomy is in English. Postings written mostly in another script are not matched."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return len(_NON_LATIN.findall(text)) / len(letters) > threshold


def requirement_text(description: str) -> str:
    """Keeps the blocks that can describe the job. Drops company descriptions and diversity statements."""
    kept = []
    for block in re.split(r"\n\s*\n", description or ""):
        if not block.strip():
            continue
        if _COMPANY_BLOCK.match(block) or _COMPANY_CLAIMS.search(block) or _EQUAL_OPPORTUNITY.search(block):
            continue
        kept.append(block)
    return "\n\n".join(kept)


def skills_for_listing(
    title: str,
    description: str,
    taxonomy: Iterable[Skill],
    cfg: SearchConfig = SearchConfig(),
) -> tuple[SkillReq, ...]:
    """Deterministic step of listing skill extraction: canonical names and aliases only.

    A skill named in the title is a must-have at the default must level. A skill named only
    in the job text is nice-to-have at the default nice level. Matches are whole-word, so
    "java" does not match "javascript". Company descriptions and diversity statements are
    ignored (requirement_text). LLM extraction for phrasing the taxonomy does not list will
    come later and go through the review queue (TECHNICAL.md section 4.3).
    """
    skills = list(taxonomy)
    if is_mostly_non_latin(f"{title}\n{description}"):
        return ()
    in_title = {s.skill_id for s in skill_mentions(title, skills)}
    job_text = requirement_text(description)
    everywhere = {s.skill_id for s in skill_mentions(f"{title}\n{job_text}", skills)}
    reqs = []
    for skill in sorted(everywhere, key=lambda sid: next(s.slug for s in skills if s.skill_id == sid)):
        if skill in in_title:
            reqs.append(SkillReq(skill, cfg.default_must_level, True))
        else:
            reqs.append(SkillReq(skill, cfg.default_nice_level, False))
    return tuple(reqs)
