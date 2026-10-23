from dataclasses import dataclass
from datetime import date
import math

from core.config import AVAILABILITY_RANK, MUST_WEIGHT, NICE_WEIGHT, SCORING_VERSION, WEIGHTS, SearchConfig
from core.domain import Candidate, Evidence, Requirement, SkillReq

EVIDENCE_WEIGHTS = {"assessment": 1.0, "employer_review": 0.9, "project": 0.8, "certificate": 0.5}
SELF_DECLARED_WEIGHT = 0.2


@dataclass(frozen=True)
class ScoreResult:
    score: float
    band: str
    confidence: float
    confidence_label: str
    components: dict[str, float]
    gate_applied: bool
    sem_scale: str
    scoring_version: str = SCORING_VERSION


def importance(sr: SkillReq) -> float:
    return MUST_WEIGHT if sr.must else NICE_WEIGHT


def coverage(sr: SkillReq, cand: Candidate) -> float:
    ps = cand.skills.get(sr.skill_id)
    if ps is None or ps.level <= 0:
        return 0.0
    return min(ps.level / sr.level, 1.0)


def is_matched(sr: SkillReq, cand: Candidate) -> bool:
    return coverage(sr, cand) > 0


def s_skill(req: Requirement, cand: Candidate) -> float:
    total = sum(importance(sr) for sr in req.skills)
    if total == 0:
        return 0.0
    return sum(importance(sr) * coverage(sr, cand) for sr in req.skills) / total


def evidence_weight(ev: Evidence) -> float:
    if not ev.verified:
        return SELF_DECLARED_WEIGHT
    return EVIDENCE_WEIGHTS.get(ev.type, SELF_DECLARED_WEIGHT)


def best_evidence_weight(skill_id: str, cand: Candidate) -> float:
    best = SELF_DECLARED_WEIGHT
    for ev in cand.evidence:
        if ev.skill_id == skill_id:
            best = max(best, evidence_weight(ev))
    return best


def s_evid(req: Requirement, cand: Candidate) -> float:
    matched = [sr for sr in req.skills if is_matched(sr, cand)]
    total = sum(importance(sr) for sr in matched)
    if total == 0:
        return 0.0
    return sum(importance(sr) * best_evidence_weight(sr.skill_id, cand) for sr in matched) / total


def months_since(last: date, as_of: date) -> int:
    return max(0, (as_of.year - last.year) * 12 + (as_of.month - last.month))


def freshness(last_used: date | None, as_of: date, cfg: SearchConfig) -> float:
    if last_used is None:
        return cfg.freshness_floor
    months = months_since(last_used, as_of)
    return max(cfg.freshness_floor, 0.5 ** (months / cfg.freshness_half_life_months))


def s_fresh(req: Requirement, cand: Candidate, as_of: date, cfg: SearchConfig) -> float:
    matched = [sr for sr in req.skills if is_matched(sr, cand)]
    if not matched:
        return cfg.freshness_floor
    total = sum(importance(sr) for sr in matched)
    return sum(
        importance(sr) * freshness(cand.skills[sr.skill_id].last_used, as_of, cfg) for sr in matched
    ) / total


def _location_fit(req: Requirement, cand: Candidate) -> float:
    city_match = bool(
        req.location_city and cand.location_city
        and req.location_city.lower() == cand.location_city.lower()
    )
    region_match = bool(
        req.location_region and cand.location_region
        and req.location_region.lower() == cand.location_region.lower()
    )
    if city_match or region_match:
        return 1.0
    if req.country and cand.country == req.country:
        return 0.5
    return 0.0


def _pay_overlaps(req: Requirement, cand: Candidate) -> bool:
    req_lo = -math.inf if req.pay_min is None else req.pay_min
    req_hi = math.inf if req.pay_max is None else req.pay_max
    cand_lo = -math.inf if cand.pay_min is None else cand.pay_min
    cand_hi = math.inf if cand.pay_max is None else cand.pay_max
    return cand_lo <= req_hi and req_lo <= cand_hi


def s_fit(req: Requirement, cand: Candidate, cfg: SearchConfig) -> float:
    checks: list[float] = []
    if req.location_city or req.location_region:
        checks.append(_location_fit(req, cand))
    if req.availability:
        meets = cand.availability is not None and (
            AVAILABILITY_RANK[cand.availability] <= AVAILABILITY_RANK[req.availability]
        )
        checks.append(1.0 if meets else 0.0)
    if req.languages:
        checks.append(len(req.languages & cand.languages) / len(req.languages))
    req_has_pay = req.pay_min is not None or req.pay_max is not None
    cand_has_pay = cand.pay_min is not None or cand.pay_max is not None
    if req_has_pay and cand_has_pay:
        checks.append(1.0 if _pay_overlaps(req, cand) else 0.0)
    if not checks:
        return cfg.neutral_fit
    return sum(checks) / len(checks)


def sem_minmax(raws: dict[str, float | None], cfg: SearchConfig) -> dict[str, float]:
    values = [v for v in raws.values() if v is not None]
    if len(values) < 2 or max(values) == min(values):
        return {k: (cfg.neutral_sem if v is not None else 0.0) for k, v in raws.items()}
    lo, hi = min(values), max(values)
    return {k: (0.0 if v is None else (v - lo) / (hi - lo)) for k, v in raws.items()}


def sem_absolute(raw: float) -> float:
    return min(max((raw + 1.0) / 2.0, 0.0), 1.0)


def gate_applied(req: Requirement, cand: Candidate) -> bool:
    return any(coverage(sr, cand) == 0 for sr in req.skills if sr.must)


def band_for(score: float) -> str:
    if score >= 80:
        return "strong"
    if score >= 60:
        return "good"
    if score >= 40:
        return "partial"
    return "weak"


def confidence(req: Requirement, cand: Candidate) -> float:
    targets = [sr for sr in req.skills if sr.must] or list(req.skills)
    if not targets:
        return 0.0
    total = 0.0
    for sr in targets:
        evs = [ev for ev in cand.evidence if ev.skill_id == sr.skill_id]
        if any(ev.verified for ev in evs):
            total += 1.0
        elif evs:
            total += 0.5
    return total / len(targets)


def confidence_label(value: float) -> str:
    if value >= 0.75:
        return "high"
    if value >= 0.4:
        return "medium"
    return "low"


def compute_score(
    req: Requirement,
    cand: Candidate,
    *,
    s_sem: float,
    sem_scale: str,
    as_of: date,
    cfg: SearchConfig = SearchConfig(),
) -> ScoreResult:
    components = {
        "sem": s_sem,
        "skill": s_skill(req, cand),
        "evid": s_evid(req, cand),
        "fresh": s_fresh(req, cand, as_of, cfg),
        "fit": s_fit(req, cand, cfg),
    }
    raw = 100.0 * sum(WEIGHTS[k] * v for k, v in components.items())
    gated = gate_applied(req, cand)
    if gated:
        raw = min(raw, cfg.gate_cap)
    score = round(raw, 1)
    conf = confidence(req, cand)
    return ScoreResult(
        score=score,
        band=band_for(score),
        confidence=conf,
        confidence_label=confidence_label(conf),
        components=components,
        gate_applied=gated,
        sem_scale=sem_scale,
    )
