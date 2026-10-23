from pathlib import Path

import pytest

from api.asgi import build_services
from core.settings import Settings, SettingsError

REPO = Path(__file__).resolve().parents[2]


def test_production_refuses_to_start_until_the_store_exists():
    with pytest.raises(SettingsError, match="production store is not built"):
        build_services({"APP_ENV": "production", "DATABASE_URL": "postgresql://x"})


def test_production_needs_a_database_url():
    with pytest.raises(SettingsError, match="DATABASE_URL is required"):
        Settings.from_env({"APP_ENV": "production"})


def test_render_blueprint_routes_api_before_the_single_page_fallback():
    text = (REPO / "infra" / "render.yaml").read_text(encoding="utf-8")
    api_rule = text.index("source: /v1/*")
    spa_rule = text.index("source: /*")
    assert api_rule < spa_rule
