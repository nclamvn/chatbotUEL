import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL


def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS claims (
    claim_id      TEXT PRIMARY KEY,
    entity        TEXT NOT NULL,
    field         TEXT NOT NULL,
    value         JSONB,
    evidence_span TEXT NOT NULL,
    extraction    TEXT NOT NULL,
    tier          TEXT NOT NULL CHECK (tier IN ('A','B','C')),
    url           TEXT NOT NULL,
    fetched_at    TEXT NOT NULL,
    snapshot      TEXT NOT NULL,
    source        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registry_cells (
    entity     TEXT NOT NULL,
    field      TEXT NOT NULL,
    status     TEXT NOT NULL CHECK (status IN ('corroborated','sourced','disputed','null')),
    value_json JSONB,
    claim_ids  JSONB NOT NULL DEFAULT '[]',
    PRIMARY KEY (entity, field)
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id   TEXT PRIMARY KEY,
    text       TEXT NOT NULL,
    url        TEXT NOT NULL,
    snapshot   TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    tier       TEXT NOT NULL CHECK (tier IN ('A','B','C')),
    embedding  vector(384)
);

CREATE TABLE IF NOT EXISTS telemetry_events (
    id           BIGSERIAL PRIMARY KEY,
    ts           TIMESTAMPTZ NOT NULL DEFAULT now(),
    session_hash TEXT NOT NULL,
    question     TEXT NOT NULL,
    normalized   TEXT NOT NULL,
    status       TEXT NOT NULL,
    citations    JSONB NOT NULL DEFAULT '[]',
    thumbs       TEXT,
    comment      TEXT
);

CREATE TABLE IF NOT EXISTS answer_cache (
    cache_key        TEXT PRIMARY KEY,
    registry_version TEXT NOT NULL,
    answer           JSONB NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- di trú idempotent cho DB đã tồn tại trước TIP-13
ALTER TABLE telemetry_events ADD COLUMN IF NOT EXISTS comment TEXT;
"""


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()
