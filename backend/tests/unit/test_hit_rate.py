import polars as pl

from src.core.hit_rate import hit_rates


def frame(rows):
    return pl.DataFrame(rows, schema={"method": pl.Utf8, "outcome": pl.Utf8}, orient="row")


def by_method(result):
    return {r["method"]: r for r in result}


def test_counts_and_rates():
    result = hit_rates(
        frame(
            [
                ("A", "binder"),
                ("A", "binder"),
                ("A", "non_binder"),
                ("A", "no_result"),
                ("B", "binder"),
                ("B", "non_binder"),
            ]
        )
    )
    a = by_method(result)["A"]
    assert (a["binders"], a["non_binders"], a["no_result"], a["labelled"]) == (2, 1, 1, 3)
    assert a["hit_rate"] == 2 / 3
    assert by_method(result)["B"]["hit_rate"] == 0.5


def test_unlabelled_is_kept_as_its_own_group():
    result = hit_rates(frame([("unlabelled", "binder"), ("X", "non_binder")]))
    assert "unlabelled" in by_method(result)


def test_zero_binder_method_shows_zero_percent():
    row = by_method(hit_rates(frame([("Z", "non_binder"), ("Z", "non_binder")])))["Z"]
    assert row["binders"] == 0
    assert row["hit_rate"] == 0.0


def test_all_no_result_method_has_null_rate_and_sorts_last():
    result = hit_rates(frame([("N", "no_result"), ("Y", "binder")]))
    assert result[-1]["method"] == "N"
    assert result[-1]["hit_rate"] is None
    assert result[-1]["labelled"] == 0


def test_sorted_by_hit_rate_descending():
    rows = [("low", "binder"), ("low", "non_binder"), ("low", "non_binder")]
    rows += [("high", "binder"), ("high", "binder"), ("high", "non_binder")]
    assert [r["method"] for r in hit_rates(frame(rows))] == ["high", "low"]


def test_counts_sum_to_total_designs():
    rows = [("A", "binder"), ("A", "no_result"), ("unlabelled", "non_binder"), ("B", "no_result")]
    result = hit_rates(frame(rows))
    total = sum(r["binders"] + r["non_binders"] + r["no_result"] for r in result)
    assert total == len(rows)


def test_empty_input():
    assert hit_rates(frame([])) == []


def test_groups_under_20_labelled_designs_are_flagged_as_small_samples():
    rows = [("big", "binder")] * 5 + [("big", "non_binder")] * 15 + [("small", "binder")] * 19
    rows += [("only_no_result", "no_result")] * 30
    flags = {r["method"]: r["small_sample"] for r in hit_rates(frame(rows))}
    assert flags == {"big": False, "small": True, "only_no_result": True}


def test_reliable_methods_sort_before_small_samples_regardless_of_rate():
    # "tiny" looks perfect (2/2) but is a small sample; "big" has a lower rate but 20+ designs.
    rows = [("tiny", "binder"), ("tiny", "binder")]
    rows += [("big", "binder")] * 12 + [("big", "non_binder")] * 8
    methods = [r["method"] for r in hit_rates(frame(rows))]
    assert methods == ["big", "tiny"]
