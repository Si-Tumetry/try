import json
from datetime import date
from pathlib import Path

import pytest

from core.actor import Actor
from core.domain import Candidate, Listing, ProfileSkill
from core.engine.filters import passes_listing_filters
from core.errors import NotFound
from core.ingestion.demo import listing_from_record, load_snapshot
from core.services.audit import InMemoryAuditSink
from core.services.talent import TalentService
from core.store.memory import InMemoryStore
from tests.fakes import HashingEmbedder
from tests.fixtures import AS_OF, TAXONOMY, YOUTH_FIELDS

SNAPSHOT = Path(__file__).resolve().parents[1] / "demo" / "greenhouse_snapshot.json"
KENYA_YOUTH = Actor(user_id="u-kenya", role="youth", scopes=frozenset({"read:public"}))


def _kenya_candidate(embedder):
    text = "Data analyst in Nairobi who works with spreadsheets and dashboards"
    return Candidate(
        profile_id="p-kenya", owner_user_id="u-kenya", country="KE", status="active", searchable=True,
        headline=text, bio="", document_text=text, availability="now",
        location_city="Nairobi", location_region="Nairobi",
        skills={"s-data-entry": ProfileSkill("s-data-entry", 3, date(2026, 6, 1))},
        employer_fields=YOUTH_FIELDS, public_fields=YOUTH_FIELDS,
        embedding=embedder.embed(text),
    )


def _service(app_env, embedder=None):
    embedder = embedder or HashingEmbedder()
    listings = load_snapshot(SNAPSHOT, app_env=app_env, embedder=embedder)
    store = InMemoryStore(skills=TAXONOMY, candidates=[_kenya_candidate(embedder)], listings=listings)
    service = TalentService(store=store, audit=InMemoryAuditSink(), embedder=embedder, clock=lambda: AS_OF)
    return service, listings


def _listing(**kw):
    base = dict(
        listing_id="l", owner_user_id="o", type="job", title="t", description="d" * 60,
        country="KE", status="active", eligible_countries=("KE",), scope="in_region",
    )
    base.update(kw)
    return Listing(**base)


# --- filter rule ------------------------------------------------------------

def test_default_view_requires_in_country_scope():
    assert passes_listing_filters(_listing(), "KE")
    assert not passes_listing_filters(_listing(), "NG")


def test_remote_listing_counts_only_when_the_country_is_named():
    remote = _listing(scope="remote_in_region", eligible_countries=("KE", "NG"))
    assert passes_listing_filters(remote, "NG")
    assert not passes_listing_filters(_listing(scope="remote_outside_region", eligible_countries=("KE",)), "KE")


def test_outside_region_listing_hidden_by_default_but_visible_globally():
    listing = _listing(scope="outside_region", eligible_countries=("GB",), country="GB")
    assert not passes_listing_filters(listing, "KE")
    assert passes_listing_filters(listing, "KE", include_global=True)


def test_no_country_means_no_default_results():
    assert not passes_listing_filters(_listing(), None)


def test_listing_awaiting_review_never_shows():
    listing = _listing(needs_review=True)
    assert not passes_listing_filters(listing, "KE")
    assert not passes_listing_filters(listing, "KE", include_global=True)


def test_paused_or_deleted_listings_never_show():
    assert not passes_listing_filters(_listing(status="paused"), "KE", include_global=True)
    assert not passes_listing_filters(_listing(deleted=True), "KE", include_global=True)


# --- service over the real snapshot ------------------------------------------

def test_kenyan_youth_sees_only_listings_open_in_kenya_by_default():
    service, _ = _service("demo")
    out = service.search_opportunities(KENYA_YOUTH, "p-kenya", min_score=0, limit=25)
    assert out["results"], "expected Kenya-open demo listings"
    for row in out["results"]:
        assert row["in_your_country"] is True
        assert row["scope"] in ("in_region", "remote_in_region")
        assert "KE" in row["eligible_countries"]


def test_global_view_is_a_superset_and_labels_other_countries():
    service, _ = _service("demo")
    local = service.search_opportunities(KENYA_YOUTH, "p-kenya", min_score=0, limit=25)
    everything = service.search_opportunities(KENYA_YOUTH, "p-kenya", include_global=True, min_score=0, limit=25)
    assert everything["total_matching"] > local["total_matching"]
    assert all(r["in_your_country"] is True for r in local["results"])
    assert any(r["in_your_country"] is False for r in everything["results"])


def test_score_does_not_depend_on_scope():
    service, _ = _service("demo")
    local = service.search_opportunities(KENYA_YOUTH, "p-kenya", min_score=0, limit=25)
    everything = service.search_opportunities(KENYA_YOUTH, "p-kenya", include_global=True, min_score=0, limit=25)
    local_scores = {r["listing_id"]: r["score"] for r in local["results"]}
    for row in everything["results"]:
        if row["listing_id"] in local_scores:
            assert row["score"] == local_scores[row["listing_id"]]


def test_results_carry_provenance_for_clients_to_label():
    service, _ = _service("demo")
    out = service.search_opportunities(KENYA_YOUTH, "p-kenya", min_score=0, limit=5)
    row = out["results"][0]
    assert row["demo"] is True
    assert row["source"].startswith("greenhouse-")
    assert row["source_url"].startswith("https://")
    assert row["employer"]


def test_review_items_never_appear_even_globally():
    service, listings = _service("demo")
    held_ids = {l.listing_id for l in listings if l.needs_review}
    assert held_ids
    out = service.search_opportunities(KENYA_YOUTH, "p-kenya", include_global=True, min_score=0, limit=25)
    assert not held_ids & {r["listing_id"] for r in out["results"]}


def test_unapproved_ingested_listings_never_appear():
    embedder = HashingEmbedder()
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    unapproved = [
        listing_from_record(rec, approve_for_demo=False, embedder=embedder)
        for rec in data["listings"]
        if rec["status"] == "ok"
    ]
    assert unapproved and all(l.status == "pending_review" for l in unapproved)
    store = InMemoryStore(skills=TAXONOMY, candidates=[_kenya_candidate(embedder)], listings=unapproved)
    svc = TalentService(store=store, audit=InMemoryAuditSink(), embedder=embedder, clock=lambda: AS_OF)
    out = svc.search_opportunities(KENYA_YOUTH, "p-kenya", include_global=True, min_score=0, limit=25)
    assert out["results"] == []


def test_other_users_cannot_run_opportunity_search_for_a_profile():
    service, _ = _service("demo")
    stranger = Actor(user_id="u-other", role="youth", scopes=frozenset({"read:public"}))
    with pytest.raises(NotFound):
        service.search_opportunities(stranger, "p-kenya", min_score=0)


def test_country_override_is_no_longer_accepted():
    service, _ = _service("demo")
    with pytest.raises(TypeError):
        service.search_opportunities(KENYA_YOUTH, "p-kenya", country="NG")
