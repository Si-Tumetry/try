import re
from pathlib import Path

import pytest

from core.settings import Settings, SettingsError, read_dotenv

BACKEND = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = BACKEND / ".env.example"


def test_defaults_when_nothing_is_set():
    s = Settings.from_env({})
    assert s.app_env == "dev"
    assert s.embedding_dim == 1024
    assert s.min_score_default == 40
    assert s.rrf_k == 60
    assert s.ingest_contact is None


def test_values_are_read_and_blank_values_ignored():
    s = Settings.from_env({"APP_ENV": "demo", "EMBEDDING_DIM": "512", "DATABASE_URL": "  "})
    assert s.app_env == "demo"
    assert s.embedding_dim == 512
    assert s.database_url is None


@pytest.mark.parametrize("env", ["prod", "Production", "live"])
def test_unknown_app_env_is_refused(env):
    with pytest.raises(SettingsError):
        Settings.from_env({"APP_ENV": env})


@pytest.mark.parametrize("name, value", [("EMBEDDING_DIM", "big"), ("RRF_K", "1.5"), ("MATCH_MIN_SCORE_DEFAULT", "forty")])
def test_non_numeric_values_are_refused(name, value):
    with pytest.raises(SettingsError):
        Settings.from_env({name: value})


def test_score_default_out_of_range_is_refused():
    with pytest.raises(SettingsError):
        Settings.from_env({"MATCH_MIN_SCORE_DEFAULT": "101"})


def test_production_requires_a_database_url():
    with pytest.raises(SettingsError, match="DATABASE_URL"):
        Settings.from_env({"APP_ENV": "production"})


def test_ingest_contact_must_be_an_email_before_live_fetches():
    with pytest.raises(SettingsError, match="email"):
        Settings.from_env({"YPP_INGEST_CONTACT": "someone"}).require_ingest_contact()
    assert Settings.from_env({"YPP_INGEST_CONTACT": "ops@example.org"}).require_ingest_contact() == "ops@example.org"


def test_dotenv_reader_skips_comments_and_strips_quotes(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "# a comment\n\nAPP_ENV=demo\nYPP_INGEST_CONTACT=\"ops@example.org\"\nSTORAGE_BUCKET='ypp-uploads'\nbroken line\n",
        encoding="utf-8",
    )
    assert read_dotenv(path) == {
        "APP_ENV": "demo",
        "YPP_INGEST_CONTACT": "ops@example.org",
        "STORAGE_BUCKET": "ypp-uploads",
    }


def test_missing_dotenv_file_is_not_an_error(tmp_path):
    assert read_dotenv(tmp_path / "absent.env") == {}


def test_every_variable_marked_used_in_env_example_is_read_by_settings():
    settings_source = (BACKEND / "core" / "settings.py").read_text(encoding="utf-8")
    used: list[str] = []
    marked = False
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            marked = marked or "[used]" in line
            continue
        match = re.match(r"^([A-Z_]+)=", line)
        if match and marked:
            used.append(match.group(1))
        if match or not line.strip():
            marked = False
    assert used, "expected at least one variable marked [used]"
    for name in used:
        assert f'"{name}"' in settings_source, f"{name} is marked used but settings.py does not read it"


def test_env_example_has_no_real_secrets():
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "AKIA" not in text
    assert "BEGIN PRIVATE KEY" not in text
    assert "@example.org" in text or "@yourdomain.org" in text
