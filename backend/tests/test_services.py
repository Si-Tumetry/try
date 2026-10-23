import json
import re

import pytest

from core.actor import Actor
from core.errors import NotFound, PermissionDenied, ValidationFailed
from core.services.audit import InMemoryAuditSink
from core.services.talent import TalentService
from tests.fakes import FailingEmbedder, HashingEmbedder
from tests.fixtures import AS_OF, build_store

EMPLOYER = Actor(
    user_id="u-emp1", role="employer",
    scopes=frozenset({"read:candidates", "read:public", "write:listings"}),
)
EMPLOYER_NO_CANDIDATES = Actor(user_id="u-emp1", role="employer", scopes=frozenset({"read:public"}))
ADA = Actor(user_id="u-ada", role="youth", scopes=frozenset({"read:public"}))
OTHER_YOUTH = Actor(user_id="u-someone", role="youth", scopes=frozenset({"read:public"}))
ADMIN = Actor(user_id="u-admin", role="admin", scopes=frozenset({"read:candidates", "read:public"}))
ANON = Actor(user_id=None, role="anonymous", scopes=frozenset())


@pytest.fixture
def audit():
    return InMemoryAuditSink()


@pytest.fixture
def svc(audit):
    embedder = HashingEmbedder()
    return TalentService(
        store=build_store(embedder), audit=audit, embedder=embedder, llm=None, clock=lambda: AS_OF
    )


def test_youth_cannot_search_candidates(svc, audit):
    with pytest.raises(PermissionDenied):
        svc.search_talent(ADA, "python developer", country="NG")
    assert audit.events[-1].result == "denied"
    assert audit.events[-1].operation == "search_talent"


def test_search_requires_candidates_scope(svc):
    with pytest.raises(PermissionDenied, match="read:candidates"):
        svc.search_talent(EMPLOYER_NO_CANDIDATES, "python developer", country="NG")


def test_employer_search_returns_consented_ranked_results(svc):
    out = svc.search_talent(EMPLOYER, "python developer", country="NG", min_score=0)
    assert [r["profile_id"] for r in out["results"]] == ["p-ada"]
    assert out["retrieval_channels"] == ["vector", "keyword"]
    assert out["embedding_status"] == "ok"
    assert out["rerank_status"] == "skipped"


def test_search_result_has_breakdown_and_no_contact_fields(svc):
    out = svc.search_talent(EMPLOYER, "python developer", country="NG", min_score=0)
    row = out["results"][0]
    assert set(row["breakdown"]["components"]) == {"sem", "skill", "evid", "fresh", "fit"}
    serialised = json.dumps(out).lower()
    for forbidden in ("email", "phone", "full_name", "contact"):
        assert forbidden not in serialised


def test_search_limit_above_maximum_is_rejected(svc):
    with pytest.raises(ValidationFailed):
        svc.search_talent(EMPLOYER, "python", limit=26)


def test_min_score_out_of_range_is_rejected(svc):
    with pytest.raises(ValidationFailed):
        svc.search_talent(EMPLOYER, "python", min_score=101)


def test_truncation_flag_when_more_results_than_limit(svc):
    out = svc.search_talent(EMPLOYER, "python developer", min_score=0, limit=1)
    assert len(out["results"]) == 1
    assert out["truncated"] is (out["total_matching"] > 1)


def test_search_survives_embedding_outage(audit):
    service = TalentService(
        store=build_store(), audit=audit, embedder=FailingEmbedder(), llm=None, clock=lambda: AS_OF
    )
    out = service.search_talent(EMPLOYER, "python developer", country="NG", min_score=0)
    assert out["embedding_status"] == "unavailable"
    assert out["retrieval_channels"] == ["keyword"]
    assert [r["profile_id"] for r in out["results"]] == ["p-ada"]


def test_unconsented_candidate_cannot_be_scored(svc):
    with pytest.raises(NotFound):
        svc.score_candidate(EMPLOYER, "p-thandi", query="python developer")


def test_deleted_and_suspended_candidates_cannot_be_scored(svc):
    for pid in ("p-deleted", "p-suspended"):
        with pytest.raises(NotFound):
            svc.score_candidate(EMPLOYER, pid, query="python")


def test_score_candidate_uses_absolute_semantic_scale(svc):
    out = svc.score_candidate(EMPLOYER, "p-ada", query="python developer")
    assert out["result"]["breakdown"]["sem_scale"] == "absolute"
    assert out["embedding_status"] == "ok"


def test_get_profile_returns_only_public_fields(svc):
    out = svc.get_profile(ADA, "p-wanjiru")
    assert out["untrusted_text"] == {"headline": "Python and SQL analyst in Nairobi"}
    assert out["skills"] is None
    assert out["evidence"] == []
    assert out["untrusted"] is True


def test_get_profile_for_fully_public_profile(svc):
    out = svc.get_profile(ADA, "p-ada")
    assert out["untrusted_text"]["headline"].startswith("Backend developer")
    assert {"name": "Python", "level": 4} in out["skills"]
    assert any(e["url"] for e in out["evidence"])


def test_profile_with_no_public_fields_is_not_found(svc):
    with pytest.raises(NotFound):
        svc.get_profile(ADA, "p-thandi")


def test_anonymous_cannot_read_profiles(svc):
    with pytest.raises(PermissionDenied):
        svc.get_profile(ANON, "p-ada")


def test_opportunities_for_owner(svc):
    out = svc.search_opportunities(ADA, "p-ada", min_score=0)
    ids = [r["listing_id"] for r in out["results"]]
    assert ids == ["l-backend"]
    assert "l-paused" not in ids


def test_opportunities_hidden_from_other_users(svc):
    with pytest.raises(NotFound):
        svc.search_opportunities(OTHER_YOUTH, "p-ada", min_score=0)


def test_admin_can_view_any_profile_opportunities(svc):
    out = svc.search_opportunities(ADMIN, "p-ada", min_score=0)
    assert out["results"]


def test_employer_cannot_run_opportunity_search(svc):
    with pytest.raises(PermissionDenied):
        svc.search_opportunities(EMPLOYER, "p-ada", min_score=0)


def test_skill_gap_lists_missing_must_have_with_projects(svc):
    out = svc.get_skill_gap(ADA, "l-records", "p-ada")
    missing = {row["name"]: row for row in out["missing_skills"]}
    assert "Data entry" in missing
    assert missing["Data entry"]["must_have"] is True
    assert any(p["for_skill"] == "Data entry" for p in out["projects"])


def test_skill_gap_for_other_users_profile_is_not_found(svc):
    with pytest.raises(NotFound):
        svc.get_skill_gap(OTHER_YOUTH, "l-backend", "p-ada")


def test_list_skills_filters_by_query_and_alias(svc):
    out = svc.list_skills(ADA, query="postgres")
    assert [s["slug"] for s in out["skills"]] == ["sql"]


def test_list_skills_filters_by_category(svc):
    out = svc.list_skills(ADA, category="service")
    assert [s["slug"] for s in out["skills"]] == ["customer-service"]


def test_list_skills_limit_bounds(svc):
    with pytest.raises(ValidationFailed):
        svc.list_skills(ADA, limit=0)


def test_audit_records_success_without_raw_arguments(svc, audit):
    svc.search_talent(EMPLOYER, "confidential hiring plan for python", country="NG", min_score=0)
    event = audit.events[-1]
    assert event.result == "ok"
    assert event.actor_id == "u-emp1"
    assert event.door == "mcp"
    assert re.fullmatch(r"[0-9a-f]{64}", event.args_hash)
    assert "confidential" not in event.args_hash


def test_audit_records_not_found(svc, audit):
    with pytest.raises(NotFound):
        svc.score_candidate(EMPLOYER, "p-thandi", query="python")
    assert audit.events[-1].result == "not_found"
