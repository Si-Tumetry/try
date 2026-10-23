import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from core.ingestion.demo import EnvironmentGuard, check_environment, listing_from_record, load_snapshot
from core.ingestion.greenhouse import (
    BoardNotFound,
    GreenhouseConnector,
    GreenhouseError,
    RateLimited,
    html_to_text,
)
from core.ingestion.location import parse_location
from tests.fakes import HashingEmbedder

SNAPSHOT = Path(__file__).resolve().parents[1] / "demo" / "greenhouse_snapshot.json"
LONG = "We are hiring a support engineer to run customer tooling for our Lagos and Nairobi teams."


# --- location parsing -------------------------------------------------------

@pytest.mark.parametrize(
    "text, countries, scope, work_mode",
    [
        ("Lagos, Nigeria", ("NG",), "in_region", "onsite_or_hybrid"),
        ("Nairobi, Kenya", ("KE",), "in_region", "onsite_or_hybrid"),
        ("Remote, Kenya", ("KE",), "remote_in_region", "remote"),
        ("Remote, Lagos, Nigeria", ("NG",), "remote_in_region", "remote"),
        ("Remote, Spain", ("ES",), "remote_outside_region", "remote"),
        ("London, United Kingdom", ("GB",), "outside_region", "onsite_or_hybrid"),
        ("Cape Town, SA", ("ZA",), "in_region", "onsite_or_hybrid"),
        ("Capetown", ("ZA",), "in_region", "onsite_or_hybrid"),
        ("New York, NY", ("US",), "outside_region", "onsite_or_hybrid"),
        ("Remote", (), "unspecified", "remote"),
        ("", (), "unspecified", "unspecified"),
    ],
)
def test_location_parsing(text, countries, scope, work_mode):
    parsed = parse_location(text)
    assert parsed.eligible_countries == countries
    assert parsed.scope == scope
    assert parsed.work_mode == work_mode


def test_multi_country_remote_list_keeps_every_country():
    parsed = parse_location("Remote, India; Remote, Kenya; Remote, Lagos, Nigeria; Remote, South Africa")
    assert parsed.eligible_countries == ("IN", "KE", "NG", "ZA")
    assert parsed.scope == "remote_in_region"
    assert parsed.unmapped == ()


def test_mixed_onsite_and_remote_with_a_regional_country_is_in_region():
    parsed = parse_location("London, United Kingdom; Remote, Kenya")
    assert parsed.work_mode == "onsite_or_hybrid"
    assert parsed.scope == "in_region"


def test_unknown_region_word_is_unmapped_not_guessed():
    parsed = parse_location("Africa")
    assert parsed.eligible_countries == ()
    assert parsed.unmapped == ("Africa",)
    assert parsed.scope == "unspecified"


def test_remote_qualifier_with_unknown_place_is_unmapped():
    parsed = parse_location("US Remote")
    assert parsed.unmapped == ("US Remote",)


def test_html_to_text_decodes_double_encoded_markup():
    raw = "&amp;lt;p&amp;gt;Build things &amp;amp; ship them.&amp;lt;/p&amp;gt;"
    assert html_to_text(raw) == "Build things & ship them."


# --- connector --------------------------------------------------------------

def _job(**overrides):
    base = {
        "id": 1001,
        "title": "Support Engineer",
        "location": {"name": "Remote, Kenya"},
        "absolute_url": "https://boards.greenhouse.io/acme/jobs/1001",
        "updated_at": "2026-09-01T10:00:00-04:00",
        "application_deadline": "2026-12-01T20:00:00Z",
        "content": f"<p>{LONG}</p>",
        "departments": [{"id": 9, "name": "Engineering"}],
        "pay_input_ranges": [{"min_cents": 5000000, "max_cents": 7500000, "currency_type": "USD", "title": "Range"}],
    }
    base.update(overrides)
    return base


def _connector(handler, *, interval=0.0):
    sleeps: list[float] = []
    clock_value = [0.0]

    def clock():
        return clock_value[0]

    def sleep(seconds):
        sleeps.append(seconds)
        clock_value[0] += seconds

    connector = GreenhouseConnector(
        user_agent="YPP-Ingest/0.1 (ops@example.org)",
        min_interval_seconds=interval,
        transport=httpx.MockTransport(handler),
        clock=clock,
        sleep=sleep,
    )
    return connector, sleeps


def _board_handler(jobs, name="Acme Corp"):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/boards/acme":
            return httpx.Response(200, json={"name": name})
        if request.url.path == "/v1/boards/acme/jobs":
            assert request.url.params.get("content") == "true"
            return httpx.Response(200, json={"jobs": jobs, "meta": {"total": len(jobs)}})
        return httpx.Response(404)

    return handler


def test_connector_maps_a_valid_job_fully():
    connector, _ = _connector(_board_handler([_job()]))
    employer, drafts = connector.fetch_board("acme")
    assert employer == "Acme Corp"
    (draft,) = drafts
    assert draft.status == "ok"
    assert draft.source_key == "greenhouse-acme"
    assert draft.external_id == "1001"
    assert draft.eligible_countries == ("KE",)
    assert draft.scope == "remote_in_region"
    assert draft.expires_at == date(2026, 12, 1)
    assert draft.department == "Engineering"
    assert draft.pay_ranges[0]["min"] == 50000.0
    assert draft.pay_ranges[0]["max"] == 75000.0
    assert draft.pay_ranges[0]["currency"] == "USD"


def test_connector_rejects_short_description_and_non_https_urls():
    jobs = [
        _job(id=1, content="<p>Too short.</p>"),
        _job(id=2, absolute_url="http://boards.greenhouse.io/acme/jobs/2"),
        _job(id=3, title="   "),
        _job(id=4),
    ]
    connector, _ = _connector(_board_handler(jobs))
    _, drafts = connector.fetch_board("acme")
    by_id = {d.external_id: d for d in drafts}
    assert by_id["1"].status == "rejected" and "shorter than 50" in by_id["1"].reason
    assert by_id["2"].status == "rejected" and "https" in by_id["2"].reason
    assert by_id["3"].status == "rejected" and "missing title" in by_id["3"].reason
    assert by_id["4"].status == "ok"


def test_unmapped_location_goes_to_review_with_the_text_kept():
    connector, _ = _connector(_board_handler([_job(location={"name": "Africa"})]))
    _, drafts = connector.fetch_board("acme")
    assert drafts[0].status == "needs_review"
    assert drafts[0].unmapped_locations == ("Africa",)
    assert drafts[0].location_text == "Africa"


def test_board_not_found_is_reported():
    connector, _ = _connector(lambda request: httpx.Response(404))
    with pytest.raises(BoardNotFound):
        connector.fetch_board("acme")


def test_rate_limit_response_is_reported_with_retry_after():
    connector, _ = _connector(lambda request: httpx.Response(429, headers={"Retry-After": "30"}))
    with pytest.raises(RateLimited) as info:
        connector.fetch_board("acme")
    assert info.value.retry_after == 30.0


def test_redirects_are_refused_not_followed():
    connector, _ = _connector(lambda request: httpx.Response(302, headers={"Location": "https://evil.example/"}))
    with pytest.raises(GreenhouseError, match="redirects"):
        connector.fetch_board("acme")


def test_server_error_is_reported():
    connector, _ = _connector(lambda request: httpx.Response(503))
    with pytest.raises(GreenhouseError, match="503"):
        connector.fetch_board("acme")


def test_oversized_response_is_refused():
    big = b"x" * (2 * 1024 * 1024 + 1)
    connector, _ = _connector(lambda request: httpx.Response(200, content=big))
    with pytest.raises(GreenhouseError, match="2 MB"):
        connector.fetch_board("acme")


def test_host_allowlist_blocks_other_hosts():
    connector, _ = _connector(_board_handler([]))
    with pytest.raises(GreenhouseError, match="allowlist"):
        connector._get("https://169.254.169.254/latest/meta-data/")


def test_invalid_board_token_is_refused_before_any_request():
    calls = []
    connector, _ = _connector(lambda request: calls.append(request) or httpx.Response(200))
    with pytest.raises(GreenhouseError, match="invalid board token"):
        connector.fetch_board("../etc")
    assert calls == []


def test_requests_are_spaced_by_the_minimum_interval():
    connector, sleeps = _connector(_board_handler([_job()]), interval=5.0)
    connector.fetch_board("acme")
    assert sleeps == [5.0]


@pytest.mark.parametrize("agent", ["", "YPP-Ingest", "YPP-Ingest/0.1"])
def test_user_agent_must_carry_a_contact(agent):
    with pytest.raises(ValueError):
        GreenhouseConnector(user_agent=agent, transport=httpx.MockTransport(lambda r: httpx.Response(200)))


# --- demo guard and loader --------------------------------------------------

@pytest.mark.parametrize("env", ["production", "staging", "", "prod"])
def test_demo_data_refuses_other_environments(env):
    with pytest.raises(EnvironmentGuard):
        check_environment(env)


@pytest.mark.parametrize("env", ["dev", "demo"])
def test_demo_data_loads_in_demo_environments(env):
    check_environment(env)


def test_production_cannot_load_the_snapshot_even_by_reading_it():
    with pytest.raises(EnvironmentGuard):
        load_snapshot(SNAPSHOT, app_env="production")


def test_snapshot_loads_as_demo_listings_with_provenance():
    listings = load_snapshot(SNAPSHOT, app_env="demo", embedder=HashingEmbedder())
    assert len(listings) >= 250
    assert all(l.demo for l in listings)
    assert all(l.source_url and l.source_url.startswith("https://") for l in listings)
    assert all(l.employer_name for l in listings)
    assert all(l.embedding is not None for l in listings)
    approved = [l for l in listings if l.status == "active"]
    held = [l for l in listings if l.status == "pending_review"]
    assert approved and held
    assert all(not l.needs_review for l in approved)
    assert all(l.needs_review for l in held)


def test_snapshot_loaded_in_dev_still_leaves_review_items_unapproved():
    listings = load_snapshot(SNAPSHOT, app_env="dev")
    for listing in listings:
        if listing.needs_review:
            assert listing.status == "pending_review"


def test_snapshot_records_are_real_postings():
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert data["boards"] and data["fetched_at"]
    for rec in data["listings"]:
        assert rec["source_url"].startswith("https://")
        assert len(rec["description"]) >= 50
        assert rec["external_id"].isdigit()


def test_listing_type_is_inferred_from_title():
    rec = {
        "source_key": "greenhouse-acme", "external_id": "7", "title": "Software Engineering Intern",
        "description": LONG, "eligible_countries": ["KE"], "scope": "in_region",
        "work_mode": "onsite_or_hybrid", "source_url": "https://boards.greenhouse.io/acme/jobs/7",
        "employer_name": "Acme", "status": "ok", "unmapped_locations": [], "expires_at": None,
    }
    assert listing_from_record(rec, approve_for_demo=False).type == "internship"
