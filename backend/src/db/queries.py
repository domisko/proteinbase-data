"""Read queries used by the API. Return Polars frames or plain rows."""

from __future__ import annotations

import polars as pl
import psycopg

from src.ingest import columns as c


def latest_snapshot(conn: psycopg.Connection) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source_file, snapshot_date, licence, credit FROM snapshot "
            "ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {"source_file": row[0], "snapshot_date": row[1], "licence": row[2], "credit": row[3]}


def list_targets(conn: psycopg.Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT target, count(*) FROM outcomes GROUP BY target")
        rows = cur.fetchall()
    targets = [
        {"slug": slug, "name": c.TARGET_LABELS.get(slug, slug), "designs": n} for slug, n in rows
    ]
    main = {slug: i for i, slug in enumerate(c.MAIN_TARGETS)}
    targets.sort(key=lambda t: (main.get(t["slug"], len(main)), -t["designs"], t["slug"]))
    return targets


def target_exists(conn: psycopg.Connection, target: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM outcomes WHERE target = %s LIMIT 1", (target,))
        return cur.fetchone() is not None


def target_designs(conn: psycopg.Connection, target: str) -> pl.DataFrame:
    """One row per design of the target: design_id, method, outcome."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT d.id, d.method, o.outcome FROM outcomes o "
            "JOIN designs d ON d.id = o.design_id WHERE o.target = %s",
            (target,),
        )
        rows = cur.fetchall()
    return pl.DataFrame(
        rows,
        schema={"design_id": pl.Utf8, "method": pl.Utf8, "outcome": pl.Utf8},
        orient="row",
    )


def target_scores(conn: psycopg.Connection, target: str) -> list[dict]:
    """Metrics available for a target and how many of its designs have a value."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT s.metric, count(DISTINCT s.design_id) FROM scores s "
            "JOIN outcomes o ON o.design_id = s.design_id AND o.target = %s "
            "WHERE (s.target IS NULL OR s.target = %s) AND s.value IS NOT NULL "
            "GROUP BY s.metric ORDER BY s.metric",
            (target, target),
        )
        return [{"name": name, "designs_with_value": n} for name, n in cur.fetchall()]


def metric_values(conn: psycopg.Connection, target: str, metric: str) -> pl.DataFrame:
    """Raw score rows for one metric on the designs of a target (value null if conflicting)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT s.design_id, s.target, s.value, s.conflicting FROM scores s "
            "JOIN outcomes o ON o.design_id = s.design_id AND o.target = %s "
            "WHERE s.metric = %s AND (s.target IS NULL OR s.target = %s)",
            (target, metric, target),
        )
        rows = cur.fetchall()
    return pl.DataFrame(
        rows,
        schema={
            "design_id": pl.Utf8,
            "target": pl.Utf8,
            "value": pl.Float64,
            "conflicting": pl.Boolean,
        },
        orient="row",
    )
