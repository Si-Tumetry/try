-- DATABASE.md §4.6 and §4.7, reduced to the fields the listing domain uses.
--  * listing_key ("source_key:external_id") is the public id used in URLs and by the engine.
--  * owner_user_id is nullable. Ingested listings have no employer account yet.
--  * employer_name, department, demo, needs_review and origin are added for the directory and ingestion.

CREATE TABLE listings (
    id uuid PRIMARY KEY,
    listing_key text NOT NULL UNIQUE,
    owner_user_id uuid REFERENCES users (id),
    type text NOT NULL CHECK (type IN ('business', 'service', 'job', 'internship', 'apprenticeship')),
    title text NOT NULL CHECK (char_length(title) <= 300),
    description text NOT NULL DEFAULT '',
    country char(2) CHECK (country IS NULL OR country ~ '^[A-Z]{2}$'),
    location_text text NOT NULL DEFAULT '',
    location_city text,
    location_region text,
    eligible_countries char(2)[] NOT NULL DEFAULT '{}',
    unmapped_locations text[] NOT NULL DEFAULT '{}',
    work_mode text NOT NULL DEFAULT 'unspecified'
        CHECK (work_mode IN ('onsite', 'hybrid', 'remote', 'onsite_or_hybrid', 'unspecified')),
    scope text NOT NULL DEFAULT 'unspecified'
        CHECK (scope IN ('in_region', 'remote_in_region', 'outside_region', 'remote_outside_region', 'unspecified')),
    status text NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'pending_review', 'active', 'paused', 'closed', 'rejected')),
    needs_review boolean NOT NULL DEFAULT false,
    demo boolean NOT NULL DEFAULT false,
    origin text NOT NULL DEFAULT 'admin_import' CHECK (origin IN ('employer', 'admin_import', 'feed')),
    source_key text,
    external_id text,
    source_url text CHECK (source_url IS NULL OR source_url ~* '^https?://'),
    employer_name text,
    department text,
    pay_min numeric(14, 2),
    pay_max numeric(14, 2),
    pay_currency char(3),
    expires_at date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT ck_listings_pay CHECK (pay_min IS NULL OR pay_max IS NULL OR pay_min <= pay_max)
);

CREATE UNIQUE INDEX uq_listings_source ON listings (source_key, external_id)
    WHERE source_key IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX ix_listings_active ON listings (country, status) WHERE deleted_at IS NULL;

CREATE TABLE listing_skills (
    listing_id uuid NOT NULL REFERENCES listings (id) ON DELETE CASCADE,
    skill_id uuid NOT NULL REFERENCES skills (id),
    level smallint NOT NULL CHECK (level BETWEEN 1 AND 5),
    must_have boolean NOT NULL DEFAULT false,
    PRIMARY KEY (listing_id, skill_id)
);

CREATE INDEX ix_listing_skills_skill ON listing_skills (skill_id);
