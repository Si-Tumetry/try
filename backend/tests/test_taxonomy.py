import json
from pathlib import Path

import pytest

from core.errors import YppError
from core.ingestion.demo import load_snapshot
from core.ingestion.listing_skills import is_mostly_non_latin, requirement_text, skills_for_listing
from core.taxonomy import BLOCKED_TERMS, MIN_ALIAS_CHARS, TAXONOMY_PATH, _normalise, load_taxonomy
from tests.fakes import HashingEmbedder

SNAPSHOT = Path(__file__).resolve().parents[1] / "demo" / "greenhouse_snapshot.json"


@pytest.fixture(scope="module")
def taxonomy():
    return load_taxonomy()


def test_taxonomy_has_about_three_hundred_skills(taxonomy):
    assert 290 <= len(taxonomy) <= 320


def test_every_skill_has_a_name_category_and_path(taxonomy):
    for skill in taxonomy:
        assert skill.name and skill.category
        assert skill.taxonomy_path[0] == skill.category


def test_slugs_and_ids_are_unique_and_stable(taxonomy):
    assert len({s.slug for s in taxonomy}) == len(taxonomy)
    assert len({s.skill_id for s in taxonomy}) == len(taxonomy)
    again = load_taxonomy()
    assert [s.skill_id for s in taxonomy] == [s.skill_id for s in again]


def test_no_alias_is_short_or_a_blocked_common_word(taxonomy):
    for skill in taxonomy:
        for alias in skill.aliases:
            key = _normalise(alias)
            assert len(key) >= MIN_ALIAS_CHARS, (skill.slug, alias)
            assert key not in BLOCKED_TERMS, (skill.slug, alias)


def test_no_term_belongs_to_two_skills(taxonomy):
    owner = {}
    for skill in taxonomy:
        for term in (skill.name, *skill.aliases):
            key = _normalise(term)
            assert owner.get(key, skill.slug) == skill.slug, (key, skill.slug, owner.get(key))
            owner.setdefault(key, skill.slug)


def test_every_category_is_populated(taxonomy):
    counts = {}
    for skill in taxonomy:
        counts[skill.category] = counts.get(skill.category, 0) + 1
    assert len(counts) >= 15
    assert all(n >= 2 for n in counts.values()), counts


def _write(tmp_path, skills):
    path = tmp_path / "skills.json"
    path.write_text(json.dumps({"version": "test", "skills": skills}), encoding="utf-8")
    return path


def test_loader_rejects_duplicate_slugs(tmp_path):
    path = _write(tmp_path, [
        {"slug": "a-skill", "name": "Alpha", "path": ["X"], "aliases": []},
        {"slug": "a-skill", "name": "Beta", "path": ["X"], "aliases": []},
    ])
    with pytest.raises(YppError, match="duplicate slug"):
        load_taxonomy(path)


def test_loader_rejects_alias_collisions(tmp_path):
    path = _write(tmp_path, [
        {"slug": "one", "name": "Alpha", "path": ["X"], "aliases": ["shared term"]},
        {"slug": "two", "name": "Beta", "path": ["X"], "aliases": ["shared term"]},
    ])
    with pytest.raises(YppError, match="already belongs"):
        load_taxonomy(path)


def test_loader_rejects_short_and_blocked_aliases(tmp_path):
    short = _write(tmp_path, [{"slug": "one", "name": "Alpha", "path": ["X"], "aliases": ["ab"]}])
    with pytest.raises(YppError, match="shorter"):
        load_taxonomy(short)
    blocked = tmp_path / "blocked.json"
    blocked.write_text(json.dumps({"version": "t", "skills": [
        {"slug": "one", "name": "Alpha", "path": ["X"], "aliases": ["hiring"]}]}), encoding="utf-8")
    with pytest.raises(YppError, match="common word"):
        load_taxonomy(blocked)


def test_loader_rejects_bad_slug_and_missing_path(tmp_path):
    bad_slug = _write(tmp_path, [{"slug": "Not Valid", "name": "Alpha", "path": ["X"], "aliases": []}])
    with pytest.raises(YppError, match="invalid slug"):
        load_taxonomy(bad_slug)
    no_path = tmp_path / "nopath.json"
    no_path.write_text(json.dumps({"version": "t", "skills": [
        {"slug": "one", "name": "Alpha", "path": [], "aliases": []}]}), encoding="utf-8")
    with pytest.raises(YppError, match="path"):
        load_taxonomy(no_path)


def test_loader_rejects_missing_version(tmp_path):
    path = tmp_path / "noversion.json"
    path.write_text(json.dumps({"skills": []}), encoding="utf-8")
    with pytest.raises(YppError, match="version"):
        load_taxonomy(path)


def test_shipped_file_passes_the_loader():
    assert TAXONOMY_PATH.exists()
    assert load_taxonomy(TAXONOMY_PATH)


# --- what counts as job text -------------------------------------------------

def test_equal_opportunity_statement_is_not_matched():
    text = (
        "We build payment tools in Python.\n\n"
        "We are an equal opportunity employer. We do not discriminate on the basis of caregiving status, "
        "veteran status, or marital status."
    )
    kept = requirement_text(text)
    assert "Python" in kept
    assert "caregiving" not in kept.lower()


def test_company_heading_is_dropped_and_role_section_is_kept():
    text = (
        "About Jumia:\n\nJumia is a leading pan-African e-commerce platform.\n\n"
        "About this role\n\nYou will write SQL queries every day."
    )
    kept = requirement_text(text)
    assert "SQL" in kept
    assert "About Jumia" not in kept


def test_mostly_japanese_posting_is_not_matched_against_english_taxonomy():
    text = "Creator Consulting Manager. Walmart、Uber、Shopify、Lenovo を含む6,000以上のグローバルブランドが利用しています。"
    assert is_mostly_non_latin(text)
    assert skills_for_listing("Creator Consulting Manager", text, load_taxonomy()) == ()


def test_english_posting_is_not_treated_as_non_latin():
    assert not is_mostly_non_latin("You will write Python and SQL for the payments team.")


def test_customer_list_in_company_text_is_not_matched():
    text = (
        "impact.com is the world's leading commerce partnership platform.\n\n"
        "Today, over 5,000 global brands, including Walmart, Uber, Shopify, rely on impact.com.\n\n"
        "You will write Java services for our payments team."
    )
    kept = requirement_text(text)
    assert "Shopify" not in kept
    assert "Java" in kept


def test_about_this_role_is_kept():
    assert "Python" in requirement_text("About this role\n\nWrite Python services.")


def test_matching_uses_job_text_and_skips_company_blocks():
    taxonomy = load_taxonomy()
    by_slug = {s.slug: s.skill_id for s in taxonomy}
    reqs = skills_for_listing(
        "Engineer",
        "Our company values teamwork and honesty.\n\nYou will write Python services.",
        taxonomy,
    )
    assert {r.skill_id for r in reqs} == {by_slug["python"]}


def test_real_postings_never_match_protected_characteristic_terms():
    listings = load_snapshot(SNAPSHOT, app_env="demo", embedder=HashingEmbedder(), taxonomy=load_taxonomy())
    tax = {s.skill_id: s for s in load_taxonomy()}
    forbidden = {"caregiving"}
    for listing in listings:
        slugs = {tax[r.skill_id].slug for r in listing.skills}
        assert not slugs & forbidden, (listing.title, slugs & forbidden)


def test_full_taxonomy_gives_the_demo_real_skill_coverage():
    listings = load_snapshot(SNAPSHOT, app_env="demo", taxonomy=load_taxonomy())
    with_skills = [l for l in listings if l.skills]
    assert len(with_skills) >= 200
