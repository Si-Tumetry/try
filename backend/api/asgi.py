"""Entry point for the REST API: `uvicorn api.asgi:app --reload` from the backend folder.

Dev and demo only for now. Listings come from the demo snapshot in memory, and profiles
and tokens are lost on restart. The Postgres store (DATABASE.md) replaces both.
"""

from dataclasses import dataclass
from pathlib import Path

from starlette.applications import Starlette

from api.app import create_app
from api.auth import SessionTokens
from core.config import SearchConfig
from core.ingestion.demo import load_snapshot
from core.services.audit import InMemoryAuditSink
from core.services.profiles import ProfileService
from core.services.talent import TalentService
from core.settings import Settings, SettingsError, load_environment
from core.store.memory import InMemoryStore
from core.taxonomy import load_taxonomy

BACKEND = Path(__file__).resolve().parents[1]
DEMO_SNAPSHOT = BACKEND / "demo" / "greenhouse_snapshot.json"


@dataclass(frozen=True)
class Services:
    store: InMemoryStore
    talent: TalentService
    profiles: ProfileService
    tokens: SessionTokens


def build_services(env: dict[str, str] | None = None, snapshot: Path = DEMO_SNAPSHOT) -> Services:
    settings = Settings.from_env(env if env is not None else load_environment(BACKEND / ".env"))
    if settings.app_env not in {"dev", "demo"}:
        raise SettingsError("the production store is not built yet. Run with APP_ENV=dev or demo")

    taxonomy = load_taxonomy()
    listings = load_snapshot(snapshot, app_env=settings.app_env, taxonomy=taxonomy)
    store = InMemoryStore(skills=taxonomy, listings=listings)
    audit = InMemoryAuditSink()
    return Services(
        store=store,
        talent=TalentService(store=store, audit=audit, cfg=SearchConfig(default_min_score=settings.min_score_default)),
        profiles=ProfileService(store=store, audit=audit),
        tokens=SessionTokens(),
    )


def build_app(env: dict[str, str] | None = None, snapshot: Path = DEMO_SNAPSHOT) -> Starlette:
    parts = build_services(env, snapshot)
    return create_app(talent=parts.talent, profiles=parts.profiles, tokens=parts.tokens)


app = build_app()
