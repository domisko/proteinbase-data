"""Flatten Proteinbase CSV rows into designs, per-target outcomes and numeric scores.

Pure logic: no database or web imports. Rules are documented in
specs/001-binder-hit-rate-dashboard/data-model.md.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

import polars as pl

from src.ingest import columns as c

BINDER = "binder"
NON_BINDER = "non_binder"
NO_RESULT = "no_result"

DESIGN_SCHEMA = {
    "id": pl.Utf8,
    "source_row": pl.Int64,
    "name": pl.Utf8,
    "sequence": pl.Utf8,
    "author": pl.Utf8,
    "method": pl.Utf8,
}
OUTCOME_SCHEMA = {
    "design_id": pl.Utf8,
    "target": pl.Utf8,
    "outcome": pl.Utf8,
    "binding_strength": pl.Utf8,
}
SCORE_INPUT_SCHEMA = {
    "design_id": pl.Utf8,
    "metric": pl.Utf8,
    "target": pl.Utf8,
    "value": pl.Float64,
}
# value is null when the source recorded several different values (conflicting=True)
SCORE_SCHEMA = {**SCORE_INPUT_SCHEMA, "conflicting": pl.Boolean}
REJECTED_SCHEMA = {"source_row": pl.Int64, "reason": pl.Utf8}


@dataclass
class FlattenResult:
    designs: pl.DataFrame
    outcomes: pl.DataFrame
    scores: pl.DataFrame
    rejected: pl.DataFrame
    stats: dict[str, int] = field(default_factory=dict)


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _outcome_state(value: Any) -> str:
    if value is True:
        return BINDER
    if value is False:
        return NON_BINDER
    return NO_RESULT


def _value_type(evaluation: Mapping[str, Any]) -> str | None:
    for key in c.EVAL_VALUE_TYPE_KEYS:
        if key in evaluation:
            return evaluation[key]
    return None


def _is_numeric_score(evaluation: Mapping[str, Any]) -> bool:
    value = evaluation.get(c.EVAL_VALUE)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    value_type = _value_type(evaluation)
    return value_type is None or value_type == "numeric"


def _target(evaluation: Mapping[str, Any]) -> str | None:
    target = evaluation.get(c.EVAL_TARGET)
    if isinstance(target, str) and target.strip():
        return target.strip()
    return None


def flatten(rows: Iterable[Mapping[str, str]]) -> FlattenResult:
    """Flatten CSV rows (dicts keyed by CSV column) into tidy frames.

    ``source_row`` is the 1-based data-row number (header excluded).
    """
    designs: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    strengths: list[dict[str, Any]] = []
    scores: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    stats = {
        "rows_read": 0,
        "non_numeric_skipped": 0,
        "binding_without_target": 0,
    }

    for source_row, row in enumerate(rows, start=1):
        stats["rows_read"] += 1
        design_id = _blank_to_none(row.get(c.COL_ID))
        if design_id is None:
            rejected.append({"source_row": source_row, "reason": "missing id"})
            continue
        if design_id in seen_ids:
            rejected.append({"source_row": source_row, "reason": "duplicate id"})
            continue
        try:
            evaluations = json.loads(row.get(c.COL_EVALUATIONS) or "[]")
            if not isinstance(evaluations, list):
                raise ValueError("evaluations is not a list")
        except ValueError:
            rejected.append({"source_row": source_row, "reason": "invalid evaluations JSON"})
            continue

        seen_ids.add(design_id)
        designs.append(
            {
                "id": design_id,
                "source_row": source_row,
                "name": row.get(c.COL_NAME) or None,
                "sequence": row.get(c.COL_SEQUENCE) or None,
                "author": _blank_to_none(row.get(c.COL_AUTHOR)),
                "method": _blank_to_none(row.get(c.COL_METHOD)) or c.UNLABELLED,
            }
        )

        for evaluation in evaluations:
            if not isinstance(evaluation, dict):
                continue
            kind = evaluation.get(c.EVAL_TYPE)
            metric = evaluation.get(c.EVAL_METRIC)
            target = _target(evaluation)
            if kind == c.TYPE_EXPERIMENTAL and metric == c.METRIC_BINDING:
                if target is None:
                    stats["binding_without_target"] += 1
                    continue
                bindings.append(
                    {
                        "design_id": design_id,
                        "target": target,
                        "state": _outcome_state(evaluation.get(c.EVAL_VALUE)),
                    }
                )
            elif kind == c.TYPE_EXPERIMENTAL and metric == c.METRIC_BINDING_STRENGTH:
                value = evaluation.get(c.EVAL_VALUE)
                if target is not None and isinstance(value, str):
                    strengths.append({"design_id": design_id, "target": target, "strength": value})
            elif kind == c.TYPE_COMPUTATIONAL:
                if _is_numeric_score(evaluation) and isinstance(metric, str):
                    scores.append(
                        {
                            "design_id": design_id,
                            "metric": metric,
                            "target": target,
                            "value": float(evaluation[c.EVAL_VALUE]),
                        }
                    )
                else:
                    stats["non_numeric_skipped"] += 1

    outcomes, outcome_stats = _build_outcomes(bindings, strengths)
    score_frame, score_stats = _build_scores(scores)
    stats.update(outcome_stats)
    stats.update(score_stats)
    stats["designs"] = len(designs)
    stats["rejected_rows"] = len(rejected)

    return FlattenResult(
        designs=pl.DataFrame(designs, schema=DESIGN_SCHEMA),
        outcomes=outcomes,
        scores=score_frame,
        rejected=pl.DataFrame(rejected, schema=REJECTED_SCHEMA),
        stats=stats,
    )


def _build_outcomes(
    bindings: list[dict[str, Any]], strengths: list[dict[str, Any]]
) -> tuple[pl.DataFrame, dict[str, int]]:
    """One outcome per (design, target). Repeats collapse; disagreements become no_result."""
    binding_frame = pl.DataFrame(
        bindings,
        schema={"design_id": pl.Utf8, "target": pl.Utf8, "state": pl.Utf8},
    )
    per_pair = binding_frame.group_by(["design_id", "target"], maintain_order=True).agg(
        pl.col("state").n_unique().alias("n_states"),
        pl.col("state").first().alias("first_state"),
    )
    per_pair = per_pair.with_columns(
        pl.when(pl.col("n_states") == 1)
        .then(pl.col("first_state"))
        .otherwise(pl.lit(NO_RESULT))
        .alias("outcome")
    )

    strength_frame = pl.DataFrame(
        strengths,
        schema={"design_id": pl.Utf8, "target": pl.Utf8, "strength": pl.Utf8},
    )
    per_pair_strength = strength_frame.group_by(["design_id", "target"], maintain_order=True).agg(
        pl.col("strength").n_unique().alias("n_strengths"),
        pl.col("strength").first().alias("first_strength"),
    )
    per_pair_strength = per_pair_strength.select(
        "design_id",
        "target",
        pl.when(pl.col("n_strengths") == 1)
        .then(pl.col("first_strength"))
        .otherwise(pl.lit(None, dtype=pl.Utf8))
        .alias("binding_strength"),
    )

    outcomes = per_pair.join(per_pair_strength, on=["design_id", "target"], how="left").select(
        list(OUTCOME_SCHEMA)
    )
    mismatches = outcomes.filter(
        ((pl.col("outcome") == BINDER) & (pl.col("binding_strength") == "None"))
        | (
            (pl.col("outcome") == NON_BINDER)
            & pl.col("binding_strength").is_not_null()
            & (pl.col("binding_strength") != "None")
        )
    ).height
    stats = {
        "binding_evaluations": binding_frame.height,
        "outcome_pairs": outcomes.height,
        "conflicting_pairs": per_pair.filter(pl.col("n_states") > 1).height,
        "strength_mismatches": mismatches,
    }
    return outcomes, stats


def _build_scores(scores: list[dict[str, Any]]) -> tuple[pl.DataFrame, dict[str, int]]:
    """One row per (design, metric, target).

    Identical repeats count once. If the source recorded several *different* values for the
    same key, the outcome depends on the metric:

    - metrics listed in ``AVERAGE_WITHIN`` (ESMFold pLDDT) are averaged when the values differ by
      at most the tolerance; a wider spread is treated as conflicting;
    - every other metric is treated as conflicting.

    A conflicting row keeps a null ``value`` and ``conflicting = true`` so the design is left out
    of distributions and counted, rather than guessing a value.
    """
    frame = pl.DataFrame(scores, schema=SCORE_INPUT_SCHEMA)
    keys = ["design_id", "metric", "target"]
    grouped = frame.group_by(keys, maintain_order=True).agg(
        pl.col("value").n_unique().alias("n_values"),
        pl.col("value").first().alias("first_value"),
        pl.col("value").mean().alias("mean_value"),
        (pl.col("value").max() - pl.col("value").min()).alias("spread"),
    )
    tolerance = pl.col("metric").replace_strict(
        c.AVERAGE_WITHIN, default=None, return_dtype=pl.Float64
    )
    grouped = grouped.with_columns(
        pl.when(pl.col("n_values") == 1)
        .then(pl.lit("single"))
        .when(tolerance.is_not_null() & (pl.col("spread") <= tolerance))
        .then(pl.lit("averaged"))
        .otherwise(pl.lit("conflicting"))
        .alias("resolution")
    ).with_columns(
        (pl.col("resolution") == "conflicting").alias("conflicting"),
        pl.when(pl.col("resolution") == "single")
        .then(pl.col("first_value"))
        .when(pl.col("resolution") == "averaged")
        .then(pl.col("mean_value"))
        .otherwise(None)
        .alias("value"),
    )
    stats = {
        "score_evaluations": frame.height,
        "scores_kept": grouped.filter(~pl.col("conflicting")).height,
        "scores_averaged": grouped.filter(pl.col("resolution") == "averaged").height,
        "score_conflicts": grouped.filter(pl.col("conflicting")).height,
    }
    return grouped.select(list(SCORE_SCHEMA)), stats
