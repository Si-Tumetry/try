from dataclasses import dataclass

SCORING_VERSION = "v1"

SUPPORTED_COUNTRIES = frozenset({"NG", "ZA", "KE", "GH"})

AVAILABILITY_RANK = {"now": 0, "within_30_days": 1, "flexible": 2}

WEIGHTS = {"sem": 0.35, "skill": 0.30, "evid": 0.20, "fresh": 0.10, "fit": 0.05}

MUST_WEIGHT = 1.0
NICE_WEIGHT = 0.4


@dataclass(frozen=True)
class SearchConfig:
    vector_candidates: int = 200
    keyword_candidates: int = 200
    score_top_n: int = 100
    rerank_top_n: int = 30
    rrf_k: int = 60
    gate_cap: float = 40.0
    freshness_half_life_months: float = 24.0
    freshness_floor: float = 0.3
    neutral_sem: float = 0.5
    neutral_fit: float = 0.5
    llm_attempts: int = 2
    default_must_level: int = 3
    default_nice_level: int = 2
    default_min_score: int = 40
    max_limit: int = 25
    max_skills_param: int = 20
    max_query_chars: int = 500
