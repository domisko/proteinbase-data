import polars as pl

from src.core.distributions import distribution, select_scores


def outcomes(rows):
    return pl.DataFrame(rows, schema={"design_id": pl.Utf8, "outcome": pl.Utf8}, orient="row")


def values(rows):
    """rows: (design_id, value) or (design_id, value, conflicting)."""
    rows = [(*r, False) if len(r) == 2 else r for r in rows]
    return pl.DataFrame(
        rows,
        schema={"design_id": pl.Utf8, "value": pl.Float64, "conflicting": pl.Boolean},
        orient="row",
    )


def test_shared_bins_group_sizes_and_exclusions():
    o = outcomes(
        [
            ("a", "binder"),
            ("b", "binder"),
            ("c", "non_binder"),
            ("d", "non_binder"),
            ("e", "no_result"),
            ("f", "binder"),
        ]
    )
    v = values([("a", 0.9), ("b", 0.8), ("c", 0.1), ("d", 0.2), ("e", 0.5)])
    result = distribution(o, v, "boltz2_iptm", bins=4)
    assert result["binder"]["n"] == 2
    assert result["non_binder"]["n"] == 2
    assert result["missing_count"] == 1  # "f" is a binder without a value
    assert result["no_result_excluded"] == 1
    assert len(result["bin_edges"]) == 5
    assert sum(result["binder"]["counts"]) == 2
    assert sum(result["non_binder"]["counts"]) == 2
    assert result["bin_edges"][0] == 0.1 and result["bin_edges"][-1] == 0.9


def test_maximum_value_lands_in_last_bin():
    o = outcomes([("a", "binder"), ("b", "non_binder")])
    result = distribution(o, values([("a", 1.0), ("b", 0.0)]), "s", bins=2)
    assert result["binder"]["counts"] == [0, 1]
    assert result["non_binder"]["counts"] == [1, 0]


def test_empty_group_is_reported():
    o = outcomes([("a", "binder")])
    result = distribution(o, values([("a", 1.0)]), "s", bins=3)
    assert result["non_binder"]["n"] == 0


def test_no_values_gives_no_bins():
    result = distribution(outcomes([("a", "binder")]), values([]), "s")
    assert result["bin_edges"] == []
    assert result["missing_count"] == 1


def test_single_value_does_not_collapse_bins():
    result = distribution(outcomes([("a", "binder")]), values([("a", 2.0)]), "s", bins=2)
    assert result["bin_edges"][0] < 2.0 < result["bin_edges"][-1]


def test_select_scores_prefers_target_specific_and_ignores_other_targets():
    scores = pl.DataFrame(
        [("a", None, 1.0), ("a", "t1", 2.0), ("b", "t2", 3.0), ("c", None, 4.0)],
        schema={"design_id": pl.Utf8, "target": pl.Utf8, "value": pl.Float64},
        orient="row",
    ).with_columns(pl.lit(False).alias("conflicting"))
    picked = {r[0]: r[1] for r in select_scores(scores, "t1").iter_rows()}
    assert picked == {"a": 2.0, "c": 4.0}


def test_conflicting_scores_are_excluded_and_counted_separately():
    o = outcomes([("a", "binder"), ("b", "binder"), ("c", "non_binder"), ("d", "non_binder")])
    v = values([("a", 0.9), ("b", None, True), ("c", 0.1)])  # d has no record at all
    result = distribution(o, v, "s", bins=2)
    assert result["binder"]["n"] == 1
    assert result["non_binder"]["n"] == 1
    assert result["conflicting_excluded"] == 1
    assert result["missing_count"] == 1
