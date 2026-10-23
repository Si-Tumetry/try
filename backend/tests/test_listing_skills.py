from pathlib import Path

from core.domain import Skill, SkillReq
from core.ingestion.demo import load_snapshot
from core.ingestion.listing_skills import skills_for_listing
from tests.fakes import HashingEmbedder
from tests.fixtures import PY, SQL, TAXONOMY

SNAPSHOT = Path(__file__).resolve().parents[1] / "demo" / "greenhouse_snapshot.json"
JAVA = Skill("s-java", "java", "Java", "Technology", ("Technology", "Software"))


def test_title_mention_is_a_must_have_at_the_default_level():
    reqs = skills_for_listing("Junior Python developer", "Build internal tools.", TAXONOMY)
    assert reqs == (SkillReq("s-python", 3, True),)


def test_description_only_mention_is_nice_to_have():
    reqs = skills_for_listing("Engineer", "You will write Python services.", TAXONOMY)
    assert reqs == (SkillReq("s-python", 2, False),)


def test_alias_matches_the_canonical_skill():
    reqs = skills_for_listing("Data role", "Strong PostgreSQL experience needed.", TAXONOMY)
    assert reqs == (SkillReq("s-sql", 2, False),)


def test_whole_word_matching_avoids_substring_hits():
    reqs = skills_for_listing("Frontend engineer", "Experience with JavaScript and React.", [JAVA])
    assert reqs == ()


def test_no_mention_means_no_skills():
    assert skills_for_listing("Receptionist", "Greet visitors and answer the phone.", TAXONOMY) == ()


def test_skill_in_title_and_description_is_counted_once_as_must():
    reqs = skills_for_listing("SQL analyst", "We use SQL every day.", TAXONOMY)
    assert reqs == (SkillReq("s-sql", 3, True),)


def test_output_is_ordered_by_slug_for_stable_snapshots():
    reqs = skills_for_listing("Python and SQL", "", TAXONOMY)
    assert [r.skill_id for r in reqs] == [PY.skill_id, SQL.skill_id]


def test_demo_snapshot_listings_pick_up_skills_from_the_taxonomy():
    listings = load_snapshot(SNAPSHOT, app_env="demo", embedder=HashingEmbedder(), taxonomy=TAXONOMY)
    with_skills = [l for l in listings if l.skills]
    assert len(with_skills) > 50
    assert any(any(r.must for r in l.skills) for l in with_skills)
    for listing in with_skills:
        assert all(r.skill_id in {s.skill_id for s in TAXONOMY} for r in listing.skills)


def test_snapshot_without_taxonomy_has_no_skills():
    listings = load_snapshot(SNAPSHOT, app_env="demo")
    assert all(l.skills == () for l in listings)
