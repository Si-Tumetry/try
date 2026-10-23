from datetime import date

import pytest

from core.config import WEIGHTS, SearchConfig
from core.domain import Candidate, Evidence, ProfileSkill, Requirement, SkillReq
from core.scoring import (
    band_for,
    compute_score,
    confidence,
    confidence_label,
    coverage,
    freshness,
    gate_applied,
    s_fit,
    s_fresh,
    s_skill,
    sem_absolute,
    sem_minmax,
)

AS_OF = date(2026, 10, 1)
CFG = SearchConfig()


def _cand(skills=None, evidence=(), **kw) -> Candidate:
    base = dict(profile_id="p", owner_user_id="u", country="NG", status="active", searchable=True)
    base.update(kw)
    return Candidate(skills=skills or {}, evidence=tuple(evidence), **base)


def _worked_example():
    req = Requirement(
        skills=(
            SkillReq("s-python", 3, True),
            SkillReq("s-sql", 3, True),
            SkillReq("s-django", 2, False),
        )
    )
    cand = _cand(
        skills={
            "s-python": ProfileSkill("s-python", 4, date(2026, 4, 1)),
            "s-sql": ProfileSkill("s-sql", 2, date(2024, 10, 1)),
            "s-django": ProfileSkill("s-django", 2, None),
        },
        evidence=(Evidence("project", True, "s-python"),),
    )
    return req, cand


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_worked_example_matches_design_document():
    req, cand = _worked_example()
    result = compute_score(req, cand, s_sem=0.64, sem_scale="minmax", as_of=AS_OF)
    assert result.components["skill"] == pytest.approx((1.0 + 2 / 3 + 0.4) / 2.4)
    assert result.components["evid"] == pytest.approx(0.45)
    assert result.components["fresh"] == pytest.approx((0.5 ** (6 / 24) + 0.5 + 0.4 * 0.3) / 2.4)
    assert result.components["fit"] == pytest.approx(0.5)
    assert result.score == 65.8
    assert result.band == "good"
    assert result.confidence == pytest.approx(0.5)
    assert result.confidence_label == "medium"
    assert result.gate_applied is False


def test_must_have_with_zero_coverage_caps_score_at_40():
    req = Requirement(skills=(SkillReq("s-python", 3, True),))
    cand = _cand(skills={}, evidence=())
    result = compute_score(req, cand, s_sem=1.0, sem_scale="minmax", as_of=AS_OF)
    assert result.gate_applied is True
    assert result.score <= 40.0


def test_nice_to_have_gap_does_not_trigger_gate():
    req = Requirement(skills=(SkillReq("s-python", 3, True), SkillReq("s-django", 2, False)))
    cand = _cand(skills={"s-python": ProfileSkill("s-python", 3, AS_OF)})
    assert gate_applied(req, cand) is False


def test_coverage_is_capped_at_one_when_level_exceeds_requirement():
    cand = _cand(skills={"s-python": ProfileSkill("s-python", 5, AS_OF)})
    assert coverage(SkillReq("s-python", 3), cand) == 1.0


def test_coverage_is_zero_for_level_zero_or_absent():
    cand = _cand(skills={"s-python": ProfileSkill("s-python", 0, AS_OF)})
    assert coverage(SkillReq("s-python", 3), cand) == 0.0
    assert coverage(SkillReq("s-sql", 3), cand) == 0.0


def test_skill_score_weights_nice_to_have_at_0_4():
    req = Requirement(skills=(SkillReq("a", 1, True), SkillReq("b", 1, False)))
    cand = _cand(skills={"a": ProfileSkill("a", 1, AS_OF)})
    assert s_skill(req, cand) == pytest.approx(1.0 / 1.4)


def test_freshness_half_life_is_24_months():
    assert freshness(date(2024, 10, 1), AS_OF, CFG) == pytest.approx(0.5)


def test_freshness_respects_floor_for_very_old_skills():
    assert freshness(date(2010, 1, 1), AS_OF, CFG) == CFG.freshness_floor


def test_freshness_unknown_date_uses_floor():
    assert freshness(None, AS_OF, CFG) == CFG.freshness_floor


def test_future_last_used_is_treated_as_current():
    assert freshness(date(2027, 1, 1), AS_OF, CFG) == 1.0


def test_fresh_defaults_to_floor_when_nothing_matches():
    req = Requirement(skills=(SkillReq("s-python", 3, True),))
    assert s_fresh(req, _cand(), AS_OF, CFG) == CFG.freshness_floor


def test_sem_minmax_scales_across_pool():
    out = sem_minmax({"a": 0.2, "b": 0.6, "c": 0.4}, CFG)
    assert out == pytest.approx({"a": 0.0, "b": 1.0, "c": 0.5})


def test_sem_minmax_single_candidate_is_neutral():
    assert sem_minmax({"a": 0.9}, CFG) == {"a": CFG.neutral_sem}


def test_sem_minmax_equal_values_are_neutral():
    assert sem_minmax({"a": 0.5, "b": 0.5}, CFG) == {"a": CFG.neutral_sem, "b": CFG.neutral_sem}


def test_sem_minmax_missing_embedding_scores_zero():
    assert sem_minmax({"a": 0.2, "b": None, "c": 0.9}, CFG)["b"] == 0.0


def test_sem_absolute_maps_cosine_to_unit_interval():
    assert sem_absolute(-1.0) == 0.0
    assert sem_absolute(0.0) == 0.5
    assert sem_absolute(1.0) == 1.0


def test_unverified_evidence_counts_as_self_declared():
    req = Requirement(skills=(SkillReq("s-python", 3, True),))
    unverified = _cand(
        skills={"s-python": ProfileSkill("s-python", 4, AS_OF)},
        evidence=(Evidence("assessment", False, "s-python"),),
    )
    from core.scoring import s_evid

    assert s_evid(req, unverified) == pytest.approx(0.2)


def test_verified_certificate_weight_is_0_5():
    from core.scoring import s_evid

    req = Requirement(skills=(SkillReq("s-python", 3, True),))
    cand = _cand(
        skills={"s-python": ProfileSkill("s-python", 4, AS_OF)},
        evidence=(Evidence("certificate", True, "s-python"),),
    )
    assert s_evid(req, cand) == pytest.approx(0.5)


@pytest.mark.parametrize(
    "score, band",
    [(100, "strong"), (80, "strong"), (79.9, "good"), (60, "good"), (59.9, "partial"), (40, "partial"), (39.9, "weak"), (0, "weak")],
)
def test_band_boundaries(score, band):
    assert band_for(score) == band


def test_confidence_full_when_all_must_have_verified():
    req = Requirement(skills=(SkillReq("a", 1, True),))
    cand = _cand(skills={"a": ProfileSkill("a", 1, AS_OF)}, evidence=(Evidence("project", True, "a"),))
    assert confidence(req, cand) == 1.0


def test_confidence_half_for_unverified_evidence():
    req = Requirement(skills=(SkillReq("a", 1, True),))
    cand = _cand(skills={"a": ProfileSkill("a", 1, AS_OF)}, evidence=(Evidence("project", False, "a"),))
    assert confidence(req, cand) == 0.5


def test_confidence_zero_without_evidence():
    req = Requirement(skills=(SkillReq("a", 1, True),))
    assert confidence(req, _cand()) == 0.0


def test_confidence_falls_back_to_nice_when_no_must_have():
    req = Requirement(skills=(SkillReq("a", 1, False),))
    cand = _cand(skills={"a": ProfileSkill("a", 1, AS_OF)}, evidence=(Evidence("project", True, "a"),))
    assert confidence(req, cand) == 1.0


@pytest.mark.parametrize("value, label", [(0.75, "high"), (0.74, "medium"), (0.4, "medium"), (0.39, "low")])
def test_confidence_labels(value, label):
    assert confidence_label(value) == label


def test_location_fit_city_match_is_full():
    req = Requirement(location_city="Lagos", country="NG")
    assert s_fit(req, _cand(location_city="lagos"), CFG) == 1.0


def test_location_fit_same_country_is_half():
    req = Requirement(location_city="Abuja", country="NG")
    assert s_fit(req, _cand(location_city="Lagos", country="NG"), CFG) == 0.5


def test_availability_fit_respects_order():
    req = Requirement(availability="within_30_days")
    assert s_fit(req, _cand(availability="now"), CFG) == 1.0
    assert s_fit(req, _cand(availability="flexible"), CFG) == 0.0


def test_language_fit_is_proportion_of_required():
    req = Requirement(languages=frozenset({"en", "tw"}))
    assert s_fit(req, _cand(languages=frozenset({"en"})), CFG) == 0.5


def test_pay_fit_requires_overlap():
    req = Requirement(pay_min=100, pay_max=200)
    assert s_fit(req, _cand(pay_min=150, pay_max=300), CFG) == 1.0
    assert s_fit(req, _cand(pay_min=300, pay_max=400), CFG) == 0.0


def test_fit_neutral_when_no_checks_apply():
    assert s_fit(Requirement(), _cand(), CFG) == CFG.neutral_fit
