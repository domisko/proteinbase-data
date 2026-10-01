"""Ingest the Proteinbase CSV snapshot: python -m src.ingest <path-to-csv>."""

from __future__ import annotations

import csv
import hashlib
import logging
import sys
from datetime import date
from pathlib import Path

import polars as pl
import psycopg

from src.core.flatten import FlattenResult, flatten
from src.db.connection import apply_schema, connect
from src.ingest.columns import CSV_ENCODING

log = logging.getLogger("ingest")

SNAPSHOT_DATE = date(2026, 1, 28)
LICENCE = "ODC-By"
CREDIT = "Adaptyv Bio, Proteinbase"
README_HINT = "See the README (section 'Getting the data') for where to download the CSV."


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path):
    csv.field_size_limit(sys.maxsize)
    with path.open(encoding=CSV_ENCODING, newline="") as fh:
        yield from csv.DictReader(fh)


def _copy(cur: psycopg.Cursor, table: str, columns: list[str], frame: pl.DataFrame) -> None:
    with cur.copy(f"COPY {table} ({', '.join(columns)}) FROM STDIN") as copy:
        for row in frame.select(columns).iter_rows():
            copy.write_row(row)


def load(conn: psycopg.Connection, path: Path, sha: str, result: FlattenResult) -> None:
    """Replace any existing snapshot with this one in a single transaction."""
    apply_schema(conn)
    with conn.transaction(), conn.cursor() as cur:
        cur.execute("DELETE FROM snapshot")
        cur.execute(
            "INSERT INTO snapshot (source_file, snapshot_date, sha256, licence, credit) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (path.name, SNAPSHOT_DATE, sha, LICENCE, CREDIT),
        )
        snapshot_id = cur.fetchone()[0]
        designs = result.designs.with_columns(pl.lit(snapshot_id).alias("snapshot_id"))
        _copy(
            cur,
            "designs",
            ["id", "snapshot_id", "source_row", "name", "sequence", "author", "method"],
            designs,
        )
        _copy(
            cur,
            "outcomes",
            ["design_id", "target", "outcome", "binding_strength"],
            result.outcomes,
        )
        _copy(
            cur, "scores", ["design_id", "metric", "target", "value", "conflicting"], result.scores
        )
        rejected = result.rejected.with_columns(pl.lit(snapshot_id).alias("snapshot_id"))
        _copy(cur, "rejected_rows", ["snapshot_id", "source_row", "reason"], rejected)


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(argv) != 1:
        print("usage: python -m src.ingest <path-to-csv>", file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.is_file():
        print(f"CSV not found: {path}\n{README_HINT}", file=sys.stderr)
        return 2

    sha = sha256_of(path)
    log.info("reading %s (sha256 %s)", path.name, sha)
    result = flatten(read_rows(path))
    for key, value in result.stats.items():
        log.info("%s: %s", key, value)
    if result.stats["conflicting_pairs"]:
        log.warning(
            "%d conflicting binding pairs recorded as no_result", result.stats["conflicting_pairs"]
        )
    if result.stats["strength_mismatches"]:
        log.warning(
            "%d binding vs binding_strength mismatches (binding kept)",
            result.stats["strength_mismatches"],
        )

    with connect() as conn:
        load(conn, path, sha, result)
    log.info("snapshot loaded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
