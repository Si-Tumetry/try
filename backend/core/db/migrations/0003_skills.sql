-- DATABASE.md §4.3. The taxonomy is reference data, loaded from backend/taxonomy/skills.json.
CREATE TABLE skills (
    id uuid PRIMARY KEY,
    slug text NOT NULL,
    name text NOT NULL,
    aliases text[] NOT NULL DEFAULT '{}',
    taxonomy_path text[] NOT NULL,
    category text NOT NULL,
    suggested_projects jsonb NOT NULL DEFAULT '[]',
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_skills_slug UNIQUE (slug),
    CONSTRAINT ck_skills_path CHECK (cardinality(taxonomy_path) >= 1)
);

CREATE UNIQUE INDEX uq_skills_lower_name ON skills (lower(name));
CREATE INDEX ix_skills_aliases ON skills USING gin (aliases);
