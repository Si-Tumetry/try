import re
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


def skill_mentions(text: str, skills: Iterable[Skill]) -> list[Skill]:
    lowered = text.lower()
    found = [
        skill
        for skill in skills
        if any(phrase_pattern(p).search(lowered) for p in (skill.name, *skill.aliases) if p.strip())
    ]
    return sorted(found, key=lambda s: s.slug)
