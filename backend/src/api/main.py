"""FastAPI app: read-only public API. No authentication."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.db.connection import connect

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("api")

NO_DATA_MESSAGE = (
    "No data loaded yet. Download the Proteinbase CSV snapshot and run the ingest command; "
    "see the README section 'Getting the data'."
)

app = FastAPI(title="Proteinbase Hit-Rate API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])


def get_conn() -> Iterator[psycopg.Connection]:
    try:
        conn = connect()
    except psycopg.OperationalError as exc:
        log.error("database unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    try:
        yield conn
    finally:
        conn.close()


def require_data(conn: psycopg.Connection = Depends(get_conn)) -> psycopg.Connection:
    """Dependency: a connection to a database that has a snapshot loaded."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM snapshot LIMIT 1")
            loaded = cur.fetchone() is not None
    except psycopg.errors.UndefinedTable:
        conn.rollback()
        loaded = False
    if not loaded:
        raise HTTPException(status_code=503, detail=NO_DATA_MESSAGE)
    return conn


from src.api import routes_meta, routes_scores, routes_targets  # noqa: E402

app.include_router(routes_meta.router)
app.include_router(routes_targets.router)
app.include_router(routes_scores.router)
