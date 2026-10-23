-- DATABASE.md §4.1 (users), with deviations recorded in docs/DATABASE.md §4.1a:
--  * google_sub identifies the account. Email is not stored.
--  * country is nullable. The member chooses it on their profile, not at sign-in.
--  * sessions and oauth_states are new: server-side sessions for Google sign-in.

CREATE TABLE users (
    id uuid PRIMARY KEY,
    google_sub text NOT NULL,
    full_name text,
    role text NOT NULL DEFAULT 'youth'
        CHECK (role IN ('youth', 'employer', 'business', 'admin', 'partner')),
    country char(2) CHECK (country IS NULL OR country IN ('NG', 'ZA', 'KE', 'GH')),
    consent_terms_version text,
    consent_terms_at timestamptz,
    suspended_at timestamptz,
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE UNIQUE INDEX uq_users_google_sub ON users (google_sub) WHERE deleted_at IS NULL;

CREATE TABLE sessions (
    token_digest text PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL
);

CREATE INDEX ix_sessions_user ON sessions (user_id);
CREATE INDEX ix_sessions_expires ON sessions (expires_at);

CREATE TABLE oauth_states (
    state_digest text PRIMARY KEY,
    nonce text NOT NULL,
    code_verifier text NOT NULL,
    next_path text NOT NULL CHECK (next_path IN ('/profile', '/dashboard')),
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL
);

CREATE INDEX ix_oauth_states_expires ON oauth_states (expires_at);
