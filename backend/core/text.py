import re
from collections import Counter
from collections.abc import Iterable
from functools import lru_cache

from core.domain import Skill

_WORD = re.compile(r"[a-z0-9][a-z0-9+#.]*")

STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "by", "can", "for", "from",
        "i", "in", "is", "looking", "need", "of", "on", "or", "someone", "the",
        "to", "we", "who", "with",
    }
)


def tokens(text: str) -> frozenset[str]:
    found = {t.rstrip(".") for t in _WORD.findall(text.lower())}
    return frozenset(t for t in found if t and t not in STOPWORDS)


@lru_cache(maxsize=4096)
def phrase_pattern(phrase: str) -> re.Pattern[str]:
    return re.compile(
        r"(?<![a-z0-9+#.])" + re.escape(phrase.lower().strip()) + r"(?![a-z0-9+#])"
    )


@lru_cache(maxsize=8)
def _matcher_for(skills: tuple[Skill, ...]) -> tuple[re.Pattern[str], dict[str, str]]:
    """One combined pattern for a whole taxonomy. Longer phrases are tried first, so "python3" beats "python"."""
    owner: dict[str, str] = {}
    for skill in skills:
        for phrase in (skill.name, *skill.aliases):
            key = phrase.lower().strip()
            if key:
                owner.setdefault(key, skill.slug)
    ordered = sorted(owner, key=len, reverse=True)
    pattern = re.compile(
        r"(?<![a-z0-9+#.])(" + "|".join(re.escape(p) for p in ordered) + r")(?![a-z0-9+#])"
    )
    return pattern, owner


def skill_mentions(text: str, skills: Iterable[Skill]) -> list[Skill]:
    skills_t = tuple(skills)
    if not skills_t or not text:
        return []
    pattern, owner = _matcher_for(skills_t)
    slugs = {owner[m.group(1)] for m in pattern.finditer(text.lower())}
    by_slug = {s.slug: s for s in skills_t}
    return sorted((by_slug[slug] for slug in slugs), key=lambda s: s.slug)


def skill_mention_counts(text: str, skills: Iterable[Skill]) -> Counter[str]:
    """How many times each skill (by slug) is named in the text."""
    skills_t = tuple(skills)
    if not skills_t or not text:
        return Counter()
    pattern, owner = _matcher_for(skills_t)
    return Counter(owner[m.group(1)] for m in pattern.finditer(text.lower()))
