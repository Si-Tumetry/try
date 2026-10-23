from datetime import date
from pathlib import Path

import pytest

from core.actor import Actor
from core.domain import Candidate, ProfileSkill
from core.errors import ValidationFailed
from core.ingestion.demo import load_snapshot
from core.pagination import decode_cursor, encode_cursor, page_of
from core.services.audit import InMemoryAuditSink
from core.services.talent import TalentService
from core.store.memory import InMemoryStore
from tests.fakes import HashingEmbedder
from tests.fixtures import AS_OF, TAXONOMY, YOUTH_FIELDS, build_store

SNAPSHOT = Path(__file__).resolve().parents[1] / "demo" / "greenhouse_snapshot.json"
EMPLOYER = Actor(user_id="u-emp1", role="employer", scopes=frozenset({"read:candidates", "read:public"}))
KENYA_YOUTH = Actor(user_id="u-kenya", role="youth", scopes=frozenset({"read:public"}))
ANY_YOUTH = Actor(user_id="u-any", role="youth", scopes=frozenset({"read:public"}))


def test_cursor_round_trip():
    for offset in (0, 1, 25, 10_000):
        assert decode_cursor(encode_cursor(offset)) == offset


def test_empty_cursor_means_first_page():
    assert decode_cursor(None) == 0
    assert decode_cursor("") == 0


@pytest.mark.parametrize(
    "bad",
    ["!!!", "bm90IGpzb24", "eyJvIjotMX0", "eyJvIjoiMSJ9", "eyJvIjp0cnVlfQ", "eyJ4IjoxfQ", "W10"],
)
def test_malformed_or_tampered_cursor_is_refused(bad):
    with pytest.raises(ValidationFailed):
        decode_cursor(bad)


def test_page_of_walks_every_item_exactly_once():
    items = list(range(7))
    seen, cursor = [], None
    while True:
        chunk, cursor = page_of(items, cursor, 3)
        seen.extend(chunk)
        if cursor is None:
            break
    assert seen == items


def test_page_of_has_no_next_cursor_on_exact_boundary():
    _, cursor = page_of([1, 2, 3], None, 3)
    assert cursor is None


def test_talent_search_pages_without_duplicates():
    embedder = HashingEmbedder()
    service = TalentService(store=build_store(embedder), audit=InMemoryAuditSink(), embedder=embedder, clock=lambda: AS_OF)
    full = service.search_talent(EMPLOYER, "python sql developer", min_score=0, limit=25)
    ids_full = [r["profile_id"] for r in full["results"]]

    paged, cursor = [], None
    while True:
        out = service.search_talent(EMPLOYER, "python sql developer", min_score=0, limit=1, cursor=cursor)
        paged.extend(r["profile_id"] for r in out["results"])
        cursor = out["next_cursor"]
        if cursor is None:
            break
    assert paged == ids_full
    assert len(paged) == len(set(paged))


def _walk_opportunities(service, include_global):
    collected, cursor = [], None
    while True:
        out = service.search_opportunities(
            KENYA_YOUTH, "p-kenya", include_global=include_global, min_score=0, limit=25, cursor=cursor
        )
        collected.extend(r["listing_id"] for r in out["results"])
        cursor = out["next_cursor"]
        if cursor is None:
            return collected, out["total_matching"]


def _kenya_service():
    embedder = HashingEmbedder()
    text = "Data analyst in Nairobi who works with spreadsheets"
    candidate = Candidate(
        profile_id="p-kenya", owner_user_id="u-kenya", country="KE", status="active", searchable=True,
        headline=text, document_text=text, availability="now",
        skills={"s-data-entry": ProfileSkill("s-data-entry", 3, date(2026, 6, 1))},
        employer_fields=YOUTH_FIELDS, public_fields=YOUTH_FIELDS, embedding=embedder.embed(text),
    )
    listings = load_snapshot(SNAPSHOT, app_env="demo", embedder=embedder)
    store = InMemoryStore(skills=TAXONOMY, candidates=[candidate], listings=listings)
    return TalentService(store=store, audit=InMemoryAuditSink(), embedder=embedder, clock=lambda: AS_OF)


def test_opportunities_page_through_every_global_listing():
    service = _kenya_service()
    collected, total = _walk_opportunities(service, include_global=True)
    assert len(collected) == total
    assert len(collected) == len(set(collected))
    assert total > 100


def test_opportunities_local_view_pages_completely_and_stays_in_country():
    service = _kenya_service()
    collected, total = _walk_opportunities(service, include_global=False)
    assert len(collected) == total == len(set(collected))
    for listing_id in collected:
        assert listing_id.startswith("greenhouse-")


def test_opportunities_reject_a_tampered_cursor():
    service = _kenya_service()
    with pytest.raises(ValidationFailed):
        service.search_opportunities(KENYA_YOUTH, "p-kenya", min_score=0, cursor="bm90")


def test_list_skills_pages_through_the_taxonomy():
    service = TalentService(store=build_store(), audit=InMemoryAuditSink(), clock=lambda: AS_OF)
    names, cursor = [], None
    while True:
        out = service.list_skills(ANY_YOUTH, limit=2, cursor=cursor)
        names.extend(s["slug"] for s in out["skills"])
        cursor = out["next_cursor"]
        if cursor is None:
            break
    assert sorted(names) == sorted(s.slug for s in TAXONOMY)
