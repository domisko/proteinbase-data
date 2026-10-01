-- Schema version 2. See specs/001-binder-hit-rate-dashboard/data-model.md
CREATE TABLE IF NOT EXISTS snapshot (
    id            SERIAL PRIMARY KEY,
    schema_version INTEGER NOT NULL DEFAULT 2,
    source_file   TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    sha256        TEXT NOT NULL,
    licence       TEXT NOT NULL,
    credit        TEXT NOT NULL,
    ingested_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS designs (
    id          TEXT PRIMARY KEY,
    snapshot_id INTEGER NOT NULL REFERENCES snapshot(id) ON DELETE CASCADE,
    source_row  INTEGER NOT NULL,
    name        TEXT,
    sequence    TEXT,
    author      TEXT,
    method      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outcomes (
    design_id        TEXT NOT NULL REFERENCES designs(id) ON DELETE CASCADE,
    target           TEXT NOT NULL,
    outcome          TEXT NOT NULL CHECK (outcome IN ('binder', 'non_binder', 'no_result')),
    binding_strength TEXT,
    PRIMARY KEY (design_id, target)
);
CREATE INDEX IF NOT EXISTS outcomes_target_idx ON outcomes (target);

CREATE TABLE IF NOT EXISTS scores (
    design_id TEXT NOT NULL REFERENCES designs(id) ON DELETE CASCADE,
    metric    TEXT NOT NULL,
    target    TEXT,
    value     DOUBLE PRECISION,           -- null when the source gave conflicting values
    conflicting BOOLEAN NOT NULL DEFAULT false
);
-- upgrade path from schema version 1 (scores are reloaded on every ingest)
ALTER TABLE scores ALTER COLUMN value DROP NOT NULL;
ALTER TABLE scores ADD COLUMN IF NOT EXISTS conflicting BOOLEAN NOT NULL DEFAULT false;
CREATE UNIQUE INDEX IF NOT EXISTS scores_unique_idx
    ON scores (design_id, metric, target) NULLS NOT DISTINCT;
CREATE INDEX IF NOT EXISTS scores_metric_idx ON scores (metric);

CREATE TABLE IF NOT EXISTS rejected_rows (
    snapshot_id INTEGER NOT NULL REFERENCES snapshot(id) ON DELETE CASCADE,
    source_row  INTEGER NOT NULL,
    reason      TEXT NOT NULL
);
