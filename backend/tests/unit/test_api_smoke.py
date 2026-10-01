"""API smoke test: routes wired to fixture data through flatten(), no database needed."""

import csv
from datetime import date

import polars as pl
import pytest
from fastapi.testclient import TestClient

from src.api.main import app, require_data
from src.core.flatten import flatten
from src.db import queries
from src.ingest.columns import CSV_ENCODING
from tests.unit.test_flatten import FIXTURE

TARGET = "nipah-glycoprotein-g"


@pytest.fixture
def client(monkeypatch):
    with FIXTURE.open(encoding=CSV_ENCODING, newline="") as fh:
        result = flatten(csv.DictReader(fh))

    def designs(_conn, target):
        return (
            result.outcomes.filter(pl.col("target") == target)
            .join(result.designs, left_on="design_id", right_on="id")
            .select("design_id", "method", "outcome")
        )

    def values(_conn, target, metric):
        return (
            result.scores.filter(pl.col("metric") == metric)
            .join(result.outcomes.filter(pl.col("target") == target), on="design_id")
            .select("design_id", pl.col("target"), "value", "conflicting")
        )

    monkeypatch.setattr(
        queries,
        "latest_snapshot",
        lambda _c: {
            "source_file": "sample.csv",
            "snapshot_date": date(2026, 1, 28),
            "licence": "ODC-By",
            "credit": "Adaptyv Bio, Proteinbase",
        },
    )
    monkeypatch.setattr(
        queries,
        "list_targets",
        lambda _c: [{"slug": TARGET, "name": "Nipah glycoprotein G", "designs": 4}],
    )
    monkeypatch.setattr(
        queries, "target_exists", lambda _c, t: t in result.outcomes["target"].to_list()
    )
    monkeypatch.setattr(queries, "target_designs", designs)
    monkeypatch.setattr(queries, "metric_values", values)
    monkeypatch.setattr(queries, "target_scores", lambda _c, t: [])
    app.dependency_overrides[require_data] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_meta_has_credit_licence_and_date(client):
    body = client.get("/meta").json()
    assert body["credit"] == "Adaptyv Bio, Proteinbase"
    assert body["licence"] == "ODC-By"
    assert body["snapshot_date"] == "2026-01-28"


def test_targets(client):
    assert client.get("/targets").json()[0]["slug"] == TARGET


def test_hit_rates_keep_unlabelled_and_sum_to_design_count(client):
    rows = client.get(f"/targets/{TARGET}/hit-rates").json()
    assert "unlabelled" in {r["method"] for r in rows}
    assert sum(r["binders"] + r["non_binders"] + r["no_result"] for r in rows) == 4


def test_small_groups_are_flagged(client):
    rows = client.get(f"/targets/{TARGET}/hit-rates").json()
    assert all(r["small_sample"] for r in rows)  # fixture methods have far fewer than 20 designs


def test_unknown_target_is_404(client):
    assert client.get("/targets/nope/hit-rates").status_code == 404


def test_distribution_reports_exclusions(client):
    body = client.get(f"/targets/{TARGET}/scores/esmfold_plddt/distribution?bins=4").json()
    assert (
        body["binder"]["n"]
        + body["non_binder"]["n"]
        + body["missing_count"]
        + body["conflicting_excluded"]
        == 3
    )
    assert body["no_result_excluded"] == 1


def test_unknown_score_is_404(client):
    assert client.get(f"/targets/{TARGET}/scores/nope/distribution").status_code == 404
