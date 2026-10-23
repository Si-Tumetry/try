from core.config import WEIGHTS
from core.domain import Candidate, Requirement, Skill
from core.engine.rag import Scored
from core.scoring import coverage


def skill_rows(req: Requirement, cand: Candidate, taxonomy: dict[str, Skill]) -> list[dict]:
    rows = []
    for sr in req.skills:
        skill = taxonomy.get(sr.skill_id)
        ps = cand.skills.get(sr.skill_id)
        rows.append(
            {
                "skill_id": sr.skill_id,
                "name": skill.name if skill else sr.skill_id,
                "must_have": sr.must,
                "required_level": sr.level,
                "level": ps.level if ps else 0,
                "coverage": round(coverage(sr, cand), 3),
            }
        )
    return rows


def matched_and_missing(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    matched = [r for r in rows if r["coverage"] > 0]
    missing = [r for r in rows if r["coverage"] < 1]
    return matched, missing


def projects_for(missing: list[dict], taxonomy: dict[str, Skill]) -> list[dict]:
    ordered = sorted(missing, key=lambda r: (not r["must_have"], r["name"]))
    out = []
    for row in ordered:
        skill = taxonomy.get(row["skill_id"])
        if skill is None:
            continue
        for project in skill.suggested_projects:
            out.append({"for_skill": row["name"], "project": project})
    return out


def evidence_links(cand: Candidate, visible: frozenset[str]) -> list[dict]:
    if "evidence" not in visible:
        return []
    return [
        {"type": ev.type, "title": ev.title, "url": ev.url}
        for ev in cand.evidence
        if ev.verified and ev.url
    ]


def breakdown(scored: Scored) -> dict:
    r = scored.result
    return {
        "components": {k: round(v, 4) for k, v in r.components.items()},
        "weights": WEIGHTS,
        "gate_applied": r.gate_applied,
        "sem_scale": r.sem_scale,
        "scoring_version": r.scoring_version,
        "embedding_missing": scored.embedding_missing,
    }


def candidate_view(
    scored: Scored,
    req: Requirement,
    taxonomy: dict[str, Skill],
    *,
    visible: frozenset[str],
) -> dict:
    cand = scored.candidate
    rows = skill_rows(req, cand, taxonomy)
    matched, missing = matched_and_missing(rows)
    return {
        "profile_id": cand.profile_id,
        "headline": cand.headline if "headline" in visible else None,
        "score": scored.result.score,
        "band": scored.result.band,
        "confidence": {"value": round(scored.result.confidence, 2), "label": scored.result.confidence_label},
        "matched_skills": matched,
        "missing_skills": missing,
        "evidence_links": evidence_links(cand, visible),
        "next_project": (projects_for(missing, taxonomy) or [None])[0],
        "rationale": scored.rationale,
        "breakdown": breakdown(scored),
    }
