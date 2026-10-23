"""Applies the SQL migrations in core/db/migrations, in name order, once each.

Run before the API starts: `python -m core.db.migrate`. Migrations are forward only. An applied
file that has changed on disk is refused, because production must match what was reviewed.
"""

import hashlib
import os
import sys
from pathlib import Path

import psycopg

from core.errors import YppError

MIGRATIONS = Path(__file__).resolve().parent / "migrations"


class MigrationError(YppError):
    code = "internal_error"


def migration_files(directory: Path = MIGRATIONS) -> list[Path]:
    files = sorted(directory.glob("*.sql"))
    names = [f.name for f in files]
    if len(set(names)) != len(names):
        raise MigrationError("duplicate migration names")
    for name in names:
        if not name[:4].isdigit() or "_" not in name:
            raise MigrationError(f"migration {name!r} must be named NNNN_description.sql")
    return files


def apply_migrations(database_url: str, directory: Path = MIGRATIONS) -> list[str]:
    applied_now: list[str] = []
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " name text PRIMARY KEY,"
            " checksum text NOT NULL,"
            " applied_at timestamptz NOT NULL DEFAULT now())"
        )
        done = {
            row[0]: row[1]
            for row in conn.execute("SELECT name, checksum FROM schema_migrations").fetchall()
        }
        for path in migration_files(directory):
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            if path.name in done:
                if done[path.name] != checksum:
                    raise MigrationError(f"{path.name} changed after it was applied. Write a new migration instead")
                continue
            with conn.transaction():
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (name, checksum) VALUES (%s, %s)",
                    (path.name, checksum),
                )
            applied_now.append(path.name)
    return applied_now


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 1
    applied = apply_migrations(url)
    print(f"applied {len(applied)} migration(s): {', '.join(applied) or 'none, already up to date'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
