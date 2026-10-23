import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from core.errors import YppError

APP_ENVIRONMENTS = frozenset({"dev", "demo", "staging", "production"})


class SettingsError(YppError):
    code = "internal_error"


def read_dotenv(path: Path) -> dict[str, str]:
    """Reads KEY=VALUE lines. Comments and blank lines are skipped. Real environment variables win."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_environment(dotenv_path: Path) -> dict[str, str]:
    return {**read_dotenv(dotenv_path), **os.environ}


@dataclass(frozen=True)
class Settings:
    app_env: str = "dev"
    ingest_contact: str | None = None
    embedding_dim: int = 1024
    min_score_default: int = 40
    rrf_k: int = 60
    database_url: str | None = None
    redis_url: str | None = None
    aws_region: str | None = None
    bedrock_embed_model_id: str | None = None
    bedrock_llm_model_id: str | None = None
    storage_bucket: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if env is None else env

        def text(name: str) -> str | None:
            value = (source.get(name) or "").strip()
            return value or None

        def integer(name: str, default: int) -> int:
            raw = text(name)
            if raw is None:
                return default
            try:
                return int(raw)
            except ValueError as exc:
                raise SettingsError(f"{name} must be a whole number") from exc

        app_env = text("APP_ENV") or "dev"
        if app_env not in APP_ENVIRONMENTS:
            raise SettingsError(f"APP_ENV must be one of {sorted(APP_ENVIRONMENTS)}")

        settings = cls(
            app_env=app_env,
            ingest_contact=text("YPP_INGEST_CONTACT"),
            embedding_dim=integer("EMBEDDING_DIM", 1024),
            min_score_default=integer("MATCH_MIN_SCORE_DEFAULT", 40),
            rrf_k=integer("RRF_K", 60),
            database_url=text("DATABASE_URL"),
            redis_url=text("REDIS_URL"),
            aws_region=text("AWS_REGION"),
            bedrock_embed_model_id=text("BEDROCK_EMBED_MODEL_ID"),
            bedrock_llm_model_id=text("BEDROCK_LLM_MODEL_ID"),
            storage_bucket=text("STORAGE_BUCKET"),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if not 1 <= self.embedding_dim <= 4096:
            raise SettingsError("EMBEDDING_DIM must be between 1 and 4096")
        if not 0 <= self.min_score_default <= 100:
            raise SettingsError("MATCH_MIN_SCORE_DEFAULT must be between 0 and 100")
        if self.rrf_k < 1:
            raise SettingsError("RRF_K must be at least 1")
        if self.app_env == "production" and self.database_url is None:
            raise SettingsError("DATABASE_URL is required in production")

    def require_ingest_contact(self) -> str:
        """The contact address sent to employers' job boards. Required before any live fetch."""
        if not self.ingest_contact or "@" not in self.ingest_contact:
            raise SettingsError("YPP_INGEST_CONTACT must be set to an email address before live fetches")
        return self.ingest_contact
