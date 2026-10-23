"""Accounts, sessions and in-flight sign-in state, in Postgres (DATABASE.md §4.1, migration 0002).

Raw session tokens and OAuth state values are never stored. Only their SHA-256 digests are, so a
database read does not reveal a session that could be replayed.
"""

import hashlib
import secrets
import uuid
from dataclasses import dataclass

from psycopg_pool import ConnectionPool


@dataclass(frozen=True)
class User:
    id: str
    google_sub: str
    full_name: str | None
    role: str
    country: str | None


@dataclass(frozen=True)
class PendingSignIn:
    nonce: str
    code_verifier: str
    next_path: str


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class AccountStore:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def upsert_google_user(self, google_sub: str, full_name: str | None) -> User:
        with self._pool.connection() as conn:
            row = conn.execute(
                "INSERT INTO users (id, google_sub, full_name, last_login_at) VALUES (%s, %s, %s, now()) "
                "ON CONFLICT (google_sub) WHERE deleted_at IS NULL DO UPDATE SET "
                "full_name = COALESCE(EXCLUDED.full_name, users.full_name), last_login_at = now(), updated_at = now() "
                "RETURNING id, google_sub, full_name, role, country",
                (str(uuid.uuid4()), google_sub, full_name),
            ).fetchone()
        return _user(row)

    def create_session(self, user_id: str, *, ttl_days: int) -> str:
        token = secrets.token_urlsafe(32)
        with self._pool.connection() as conn:
            conn.execute(
                "INSERT INTO sessions (token_digest, user_id, expires_at) "
                "VALUES (%s, %s, now() + make_interval(days => %s))",
                (digest(token), user_id, ttl_days),
            )
        return token

    def session_user(self, token: str) -> User | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT u.id, u.google_sub, u.full_name, u.role, u.country FROM sessions s "
                "JOIN users u ON u.id = s.user_id "
                "WHERE s.token_digest = %s AND s.expires_at > now() "
                "AND u.deleted_at IS NULL AND u.suspended_at IS NULL",
                (digest(token),),
            ).fetchone()
        return _user(row) if row else None

    def delete_session(self, token: str) -> None:
        with self._pool.connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token_digest = %s", (digest(token),))

    def save_pending_sign_in(self, state: str, pending: PendingSignIn, *, ttl_minutes: int) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                "INSERT INTO oauth_states (state_digest, nonce, code_verifier, next_path, expires_at) "
                "VALUES (%s, %s, %s, %s, now() + make_interval(mins => %s))",
                (digest(state), pending.nonce, pending.code_verifier, pending.next_path, ttl_minutes),
            )

    def take_pending_sign_in(self, state: str) -> PendingSignIn | None:
        """Returns and deletes the pending sign-in. A state can be used once."""
        with self._pool.connection() as conn:
            row = conn.execute(
                "DELETE FROM oauth_states WHERE state_digest = %s AND expires_at > now() "
                "RETURNING nonce, code_verifier, next_path",
                (digest(state),),
            ).fetchone()
        return PendingSignIn(nonce=row[0], code_verifier=row[1], next_path=row[2]) if row else None

    def prune_expired(self) -> None:
        with self._pool.connection() as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at <= now()")
            conn.execute("DELETE FROM oauth_states WHERE expires_at <= now()")


def _user(row) -> User:
    user_id, sub, name, role, country = row
    return User(id=str(user_id), google_sub=sub, full_name=name, role=role, country=country)
