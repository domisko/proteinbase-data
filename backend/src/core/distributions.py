"""Binder vs non-binder score distributions. Pure Polars/Python logic."""

from __future__ import annotations

from bisect import bisect_right

import polars as pl

from src.core.flatten import BINDER, NO_RESULT, NON_BINDER


def select_scores(scores: pl.DataFrame, target: str) -> pl.DataFrame:
    """One value per design for a single metric, scoped to ``target``.

    ``scores`` has ``design_id``, ``target`` (nullable), ``value`` (null when conflicting) and
    ``conflicting``. A score naming another
    target is ignored; a score for this target wins over an untargeted one.
    """
    scoped = scores.filter(pl.col("target").is_null() | (pl.col("target") == target))
    return (
        scoped.with_columns(pl.col("target").is_null().alias("_untargeted"))
        .sort("_untargeted")
        .unique(subset="design_id", keep="first", maintain_order=True)
        .select("design_id", "value", "conflicting")
    )


def distribution(outcomes: pl.DataFrame, values: pl.DataFrame, score: str, bins: int = 20) -> dict:
    """Histogram of one score for binders vs non-binders on shared bin edges.

    ``outcomes``: ``design_id``, ``outcome`` (one row per design of the target).
    ``values``: ``design_id``, ``value`` (null when conflicting), ``conflicting`` (one row per
    design that has any record of the score).
    """
    no_result_excluded = outcomes.filter(pl.col("outcome") == NO_RESULT).height
    labelled = outcomes.filter(pl.col("outcome").is_in([BINDER, NON_BINDER]))
    joined = labelled.join(values, on="design_id", how="left")
    conflicting = pl.col("conflicting").fill_null(False)
    conflicting_excluded = joined.filter(conflicting).height
    missing_count = joined.filter(pl.col("value").is_null() & ~conflicting).height
    present = joined.filter(pl.col("value").is_not_null())

    binder_values = present.filter(pl.col("outcome") == BINDER)["value"].to_list()
    non_binder_values = present.filter(pl.col("outcome") == NON_BINDER)["value"].to_list()
    everything = binder_values + non_binder_values

    if not everything:
        edges: list[float] = []
    else:
        low, high = min(everything), max(everything)
        if low == high:
            low, high = low - 0.5, high + 0.5
        step = (high - low) / bins
        edges = [low + step * i for i in range(bins)] + [high]

    return {
        "score": score,
        "bin_edges": edges,
        "binder": _group(binder_values, edges),
        "non_binder": _group(non_binder_values, edges),
        "missing_count": missing_count,
        "conflicting_excluded": conflicting_excluded,
        "no_result_excluded": no_result_excluded,
    }


def _group(values: list[float], edges: list[float]) -> dict:
    counts = [0] * max(len(edges) - 1, 0)
    for value in values:
        # the last bin is closed on the right so the maximum is included
        index = min(bisect_right(edges, value) - 1, len(counts) - 1)
        counts[index] += 1
    return {"n": len(values), "counts": counts}
