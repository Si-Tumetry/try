from dataclasses import dataclass, replace
from datetime import date

from core.config import SearchConfig
from core.domain import Candidate, Requirement
from core.engine.filters import passes_candidate_filters
from core.engine.fusion import rrf_merge
from core.engine.rerank import rerank_candidates
from core.engine.similarity import cosine, keyword_ranking, vector_ranking
from core.errors import DependencyUnavailable
from core.ports import LLM, Embedder, Store
from core.scoring import ScoreResult, compute_score, sem_absolute, sem_minmax


@dataclass(frozen=True)
class Scored:
    candidate: Candidate
    result: ScoreResult
    embedding_missing: bool = False
    rationale: str | None = None


@dataclass(frozen=True)
class SearchOutcome:
    ranked: tuple[Scored, ...]
    pool_size: int
    channels: tuple[str, ...]
    embedding_status: str
    rerank_status: str
    violations: tuple[dict, ...]


def embed_query(embedder: Embedder | None, text: str) -> tuple[tuple[float, ...] | None, str]:
    if not text.strip():
        return None, "not_requested"
    if embedder is None:
        return None, "not_configured"
    try:
        return tuple(embedder.embed(text)), "ok"
    except DependencyUnavailable:
        return None, "unavailable"


def score_against(
    req: Requirement,
    cand: Candidate,
    *,
    req_vector: tuple[float, ...] | None,
    as_of: date,
    cfg: SearchConfig,
) -> ScoreResult:
    """Single-profile scoring. Uses absolute semantic scaling so the score does not depend on other candidates."""
    if req_vector is not None and cand.embedding is not None:
        s_sem = sem_absolute(cosine(req_vector, cand.embedding))
        scale = "absolute"
    else:
        s_sem, scale = 0.0, "none"
    return compute_score(req, cand, s_sem=s_sem, sem_scale=scale, as_of=as_of, cfg=cfg)


def run_talent_search(
    req: Requirement,
    *,
    store: Store,
    embedder: Embedder | None,
    llm: LLM | None,
    as_of: date,
    cfg: SearchConfig,
    rerank: bool,
    min_score: float,
) -> SearchOutcome:
    taxonomy = {s.skill_id: s for s in store.skills()}
    pool = {c.profile_id: c for c in store.candidates() if passes_candidate_filters(c, req)}

    req_vec, embedding_status = embed_query(embedder, req.text)

    channels: list[str] = []
    rankings: list[list[str]] = []
    if req_vec is not None:
        channels.append("vector")
        rankings.append(vector_ranking(req_vec, pool.values(), cfg.vector_candidates))
    channels.append("keyword")
    rankings.append(keyword_ranking(req, pool.values(), cfg.keyword_candidates))

    fused = rrf_merge(rankings, cfg.rrf_k)[: cfg.score_top_n]
    top = [pool[pid] for pid in fused]

    if req_vec is not None:
        raws = {c.profile_id: (cosine(req_vec, c.embedding) if c.embedding is not None else None) for c in top}
        sems = sem_minmax(raws, cfg)
        scale = "minmax"
    else:
        sems = {c.profile_id: 0.0 for c in top}
        scale = "none"

    scored = [
        Scored(
            candidate=c,
            result=compute_score(req, c, s_sem=sems[c.profile_id], sem_scale=scale, as_of=as_of, cfg=cfg),
            embedding_missing=req_vec is not None and c.embedding is None,
        )
        for c in top
    ]
    scored.sort(key=lambda s: (-s.result.score, s.candidate.profile_id))

    rerank_status = "skipped"
    violations: tuple[dict, ...] = ()
    if rerank and llm is not None and scored:
        head = scored[: cfg.rerank_top_n]
        outcome = rerank_candidates(
            req, taxonomy, [s.candidate for s in head], llm, cfg.llm_attempts
        )
        by_id = {s.candidate.profile_id: s for s in head}
        reordered = [
            replace(by_id[pid], rationale=outcome.rationales.get(pid)) for pid in outcome.order
        ]
        scored = reordered + scored[cfg.rerank_top_n :]
        rerank_status = outcome.status
        violations = outcome.violations

    ranked = tuple(s for s in scored if s.result.score >= min_score)
    return SearchOutcome(
        ranked=ranked,
        pool_size=len(pool),
        channels=tuple(channels),
        embedding_status=embedding_status,
        rerank_status=rerank_status,
        violations=violations,
    )
