"""PostgreSQL connection helpers."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg

SCHEMA_FILE = Path(__file__).with_name("schema.sql")
DEFAULT_URL = "postgresql://proteinbase:proteinbase@localhost:5432/proteinbase"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_URL)


def connect() -> psycopg.Connection:
    return psycopg.connect(database_url())


def apply_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA_FILE.read_text())
    conn.commit()
