import math

from core.domain import Candidate, Requirement
from core.scoring import is_matched
from core.text import tokens


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    if len(a) != len(b):
        raise ValueError("embedding dimension mismatch")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def keyword_score(req: Requirement, cand: Candidate) -> float:
    """Stand-in for the tsvector and trigram channel. Replaced by Postgres FTS in the SQL store."""
    overlap = len(tokens(req.text) & tokens(f"{cand.headline} {cand.bio} {cand.document_text}"))
    skill_hits = sum(1 for sr in req.skills if is_matched(sr, cand))
    return float(overlap + skill_hits)


def vector_ranking(query: tuple[float, ...], candidates, limit: int) -> list[str]:
    scored = [
        (cosine(query, c.embedding), c.profile_id) for c in candidates if c.embedding is not None
    ]
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [pid for _, pid in scored[:limit]]


def keyword_ranking(req: Requirement, candidates, limit: int) -> list[str]:
    scored = [(keyword_score(req, c), c.profile_id) for c in candidates]
    scored = [t for t in scored if t[0] > 0]
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [pid for _, pid in scored[:limit]]
