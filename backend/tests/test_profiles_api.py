import pytest
from starlette.testclient import TestClient

from api.app import create_app
from api.asgi import build_services
from core.actor import Actor

CV = (
    b"Career summary: I write Python scripts that automate reports for a retail shop. "
    b"Python for data cleaning, SQL on PostgreSQL, and Microsoft Excel dashboards. "
    b"Customer service at the counter every weekday."
)


@pytest.fixture(scope="module")
def parts():
    return build_services({"APP_ENV": "dev"})


@pytest.fixture()
def client(parts):
    app = create_app(talent=parts.talent, profiles=parts.profiles, tokens=parts.tokens)
    return TestClient(app)


def _create(client, *, country="NG", consent="true", searchable="false", cv=CV, name="cv.txt"):
    files = {"cv": (name, cv, "text/plain")} if cv is not None else {}
    return client.post(
        "/v1/profiles",
        data={"country": country, "consent": consent, "searchable": searchable, "availability": "now"},
        files=files,
    )


def _auth(token: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}"}


@pytest.fixture()
def member(client):
    response = _create(client)
    assert response.status_code == 201, response.text
    return response.json()["token"]


def test_creating_a_profile_returns_a_token_and_the_skills_found_in_the_cv(client):
    response = _create(client)

    assert response.status_code == 201
    body = response.json()
    assert body["token"]
    names = {skill["name"] for skill in body["profile"]["skills"]}
    assert {"Python", "SQL", "PostgreSQL", "Microsoft Excel", "Customer service"} <= names
    assert body["profile"]["country"] == "NG"
    assert body["profile"]["searchable"] is False


def test_the_cv_text_and_file_are_not_returned(client):
    body = _create(client).json()
    assert "Career summary" not in str(body)
    assert "automate reports" not in str(body)


def test_profile_creation_needs_consent(client):
    response = _create(client, consent="false")
    assert response.status_code == 422
    assert "agree" in response.json()["error"]["message"]


def test_a_cv_with_no_known_skills_is_rejected_with_guidance(client):
    response = _create(client, cv=b"I enjoy long walks, painting and the colour blue on weekends.")
    assert response.status_code == 422
    assert "did not find any skills" in response.json()["error"]["message"]


def test_an_unsupported_file_type_is_rejected(client):
    response = _create(client, name="cv.exe")
    assert response.status_code == 422


def test_missing_cv_is_rejected(client):
    response = _create(client, cv=None)
    assert response.status_code == 422
    assert "attach your CV" in response.json()["error"]["message"]


def test_an_unsupported_country_is_rejected(client):
    response = _create(client, country="US")
    assert response.status_code == 422


def test_profile_routes_need_a_valid_token(client, member):
    assert client.get("/v1/me/profile").status_code == 401
    assert client.get("/v1/me/profile", headers=_auth("not-a-token")).status_code == 401
    assert client.get("/v1/me/profile", headers=_auth(member)).status_code == 200


def test_updating_changes_country_and_visibility_without_losing_skills(client, member):
    response = client.put(
        "/v1/me/profile",
        data={"country": "KE", "availability": "flexible", "searchable": "true"},
        headers=_auth(member),
    )

    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["country"] == "KE"
    assert profile["searchable"] is True
    assert any(skill["name"] == "Python" for skill in profile["skills"])


def test_uploading_a_new_cv_replaces_the_skills(client, member):
    response = client.put(
        "/v1/me/profile",
        data={"country": "KE", "searchable": "false"},
        files={"cv": ("cv.txt", b"Trained in first aid and childcare. First aid kit checks weekly.", "text/plain")},
        headers=_auth(member),
    )

    names = {skill["name"] for skill in response.json()["profile"]["skills"]}
    assert "First aid" in names
    assert "Python" not in names


def test_matches_are_scored_and_sorted_highest_first(client, member):
    response = client.get("/v1/me/matches?limit=25&min_score=0", headers=_auth(member))

    assert response.status_code == 200
    body = response.json()
    assert body["total_matching"] > 0
    scores = [row["score"] for row in body["results"]]
    assert scores == sorted(scores, reverse=True)
    assert len(set(scores)) > 1, "a CV should not score every job the same"
    for row in body["results"]:
        assert row["in_your_country"] is True
        assert row["band"] in {"strong", "good", "partial", "weak"}
        assert row["confidence"]["label"] in {"high", "medium", "low"}
        assert row["source_url"]


def test_matches_respect_min_score_and_limit(client, member):
    everything = client.get("/v1/me/matches?limit=25&min_score=0", headers=_auth(member)).json()
    filtered = client.get("/v1/me/matches?limit=3&min_score=20", headers=_auth(member)).json()

    assert len(filtered["results"]) <= 3
    assert all(row["score"] >= 20 for row in filtered["results"])
    assert filtered["total_matching"] <= everything["total_matching"]


def test_bad_match_parameters_are_rejected(client, member):
    assert client.get("/v1/me/matches?limit=0", headers=_auth(member)).status_code == 422
    assert client.get("/v1/me/matches?min_score=abc", headers=_auth(member)).status_code == 422
    assert client.get("/v1/me/matches?min_score=101", headers=_auth(member)).status_code == 422


def test_skill_gap_for_a_listed_job_matches_its_score(client, member):
    top = client.get("/v1/me/matches?limit=1&min_score=0", headers=_auth(member)).json()["results"][0]

    gap = client.get(f"/v1/me/matches/{top['listing_id']}", headers=_auth(member))

    assert gap.status_code == 200
    assert gap.json()["score"] == top["score"]
    assert gap.json()["band"] == top["band"]


def test_skill_gap_for_an_unknown_listing_is_not_found(client, member):
    response = client.get("/v1/me/matches/no-such-listing", headers=_auth(member))
    assert response.status_code == 404


def test_deleting_removes_the_profile_and_revokes_the_token(client, member):
    assert client.delete("/v1/me/profile", headers=_auth(member)).status_code == 204

    assert client.get("/v1/me/profile", headers=_auth(member)).status_code == 401
    assert client.get("/v1/me/matches", headers=_auth(member)).status_code == 401


def test_each_profile_only_sees_its_own_matches(client):
    first = _create(client).json()["token"]
    second = _create(client, country="ZA").json()["token"]

    own = client.get("/v1/me/profile", headers=_auth(first)).json()["profile"]
    other = client.get("/v1/me/profile", headers=_auth(second)).json()["profile"]

    assert own["profile_id"] != other["profile_id"]
    assert own["country"] == "NG"
    assert other["country"] == "ZA"


def test_a_profile_is_hidden_from_employer_search_unless_opted_in(parts, client):
    hidden = _create(client, searchable="false").json()["token"]
    visible = _create(client, searchable="true").json()["token"]
    hidden_id = client.get("/v1/me/profile", headers=_auth(hidden)).json()["profile"]["profile_id"]
    visible_id = client.get("/v1/me/profile", headers=_auth(visible)).json()["profile"]["profile_id"]
    employer = Actor(
        user_id="employer:1", role="employer", scopes=frozenset({"read:candidates", "read:public"}), door="rest"
    )

    result = parts.talent.search_talent(employer, "python", limit=25, min_score=0)
    ids = {row["profile_id"] for row in result["results"]}

    assert visible_id in ids
    assert hidden_id not in ids


def test_employer_search_results_do_not_include_names_or_contact_details(parts, client):
    _create(client, searchable="true")
    employer = Actor(
        user_id="employer:1", role="employer", scopes=frozenset({"read:candidates", "read:public"}), door="rest"
    )

    result = parts.talent.search_talent(employer, "python", limit=5, min_score=0)

    for row in result["results"]:
        assert "email" not in str(row).lower()
        assert "phone" not in str(row).lower()


def test_private_responses_are_not_cached_and_carry_security_headers(client, member):
    response = client.get("/v1/me/profile", headers=_auth(member))

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_public_health_response_carries_security_headers_without_no_store(client):
    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "cache-control" not in response.headers
