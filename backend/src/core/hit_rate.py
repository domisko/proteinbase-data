"""Hit rate by design method. Pure Polars logic."""

from __future__ import annotations

import polars as pl

from src.core.flatten import BINDER, NO_RESULT, NON_BINDER

SMALL_SAMPLE_BELOW = 20  # methods with fewer labelled designs are flagged as small samples


def hit_rates(outcomes: pl.DataFrame) -> list[dict]:
    """Aggregate one target's designs by method.

    ``outcomes`` needs the columns ``method`` and ``outcome`` (one row per design).
    ``hit_rate`` is binders / (binders + non_binders), or None when nothing is labelled.
    ``small_sample`` is true when fewer than SMALL_SAMPLE_BELOW designs have a clear result.
    Rows are ordered with reliable (non-small-sample) methods first, then by hit rate descending
    (None last), then by labelled count. A handful of binders out of two or three tested designs
    reads as a 100% hit rate but is not evidence a method works; sorting small samples below the
    reliable ones keeps that noise from dominating the default view.
    """
    if outcomes.is_empty():
        return []
    grouped = outcomes.group_by("method").agg(
        (pl.col("outcome") == BINDER).sum().alias("binders"),
        (pl.col("outcome") == NON_BINDER).sum().alias("non_binders"),
        (pl.col("outcome") == NO_RESULT).sum().alias("no_result"),
    )
    grouped = grouped.with_columns(
        (pl.col("binders") + pl.col("non_binders")).alias("labelled")
    ).with_columns(
        pl.when(pl.col("labelled") > 0)
        .then(pl.col("binders") / pl.col("labelled"))
        .otherwise(None)
        .alias("hit_rate"),
        (pl.col("labelled") < SMALL_SAMPLE_BELOW).alias("small_sample"),
    )
    grouped = grouped.sort(
        ["small_sample", "hit_rate", "labelled", "method"],
        descending=[False, True, True, False],
        nulls_last=True,
    )
    return grouped.select(
        "method", "binders", "non_binders", "no_result", "labelled", "hit_rate", "small_sample"
    ).to_dicts()
