-- DATABASE.md §4.2 and §4.4, reduced to what the profile flow stores today.
--  * country lives on the profile. The member chooses it when uploading a CV.
--  * cv_consent_at records when the member agreed to CV processing (addition).
--  * headline, bio, embeddings and search columns wait for the embedding and search work.

CREATE TABLE profiles (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users (id),
    country char(2) NOT NULL CHECK (country IN ('NG', 'ZA', 'KE', 'GH')),
    availability text CHECK (availability IS NULL OR availability IN ('now', 'within_30_days', 'flexible')),
    status text NOT NULL DEFAULT 'active'
        CHECK (status IN ('pending_extraction', 'pending_embedding', 'active', 'extraction_failed', 'suspended')),
    searchable boolean NOT NULL DEFAULT false,
    cv_consent_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

-- One live profile per user. Deleted profiles do not count, so a member can start again.
CREATE UNIQUE INDEX uq_profiles_user ON profiles (user_id) WHERE deleted_at IS NULL;

CREATE INDEX ix_profiles_filter ON profiles (status, searchable, availability) WHERE deleted_at IS NULL;

CREATE TABLE profile_skills (
    profile_id uuid NOT NULL REFERENCES profiles (id) ON DELETE CASCADE,
    skill_id uuid NOT NULL REFERENCES skills (id),
    level smallint NOT NULL CHECK (level BETWEEN 1 AND 5),
    years numeric(4, 1) CHECK (years IS NULL OR years >= 0),
    last_used date,
    source text NOT NULL DEFAULT 'self' CHECK (source IN ('self', 'assessment', 'evidence', 'endorsed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (profile_id, skill_id)
);

CREATE INDEX ix_profile_skills_skill ON profile_skills (skill_id, level);
