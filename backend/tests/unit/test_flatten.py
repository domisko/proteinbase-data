import csv
from pathlib import Path

import polars as pl

from src.core.flatten import BINDER, NO_RESULT, NON_BINDER, flatten
from src.ingest.columns import CSV_ENCODING

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample.csv"


def load_rows():
    with FIXTURE.open(encoding=CSV_ENCODING, newline="") as fh:
        return list(csv.DictReader(fh))


def outcome(result, design_id, target="nipah-glycoprotein-g"):
    row = result.outcomes.filter((pl.col("design_id") == design_id) & (pl.col("target") == target))
    assert row.height == 1
    return row.row(0, named=True)


def test_bom_is_stripped_from_first_column():
    assert list(load_rows()[0])[0] == "id"


def test_repeated_identical_binding_evaluations_count_once():
    result = flatten(load_rows())
    pairs = result.outcomes.filter(pl.col("design_id") == "a")
    assert pairs.height == 1
    assert pairs["outcome"][0] == BINDER
    # three identical evaluations for "a" still collapse into one pair
    assert result.stats["binding_evaluations"] > result.stats["outcome_pairs"]


def test_conflicting_evaluations_become_no_result_and_are_counted():
    result = flatten(load_rows())
    assert outcome(result, "c")["outcome"] == NO_RESULT
    assert result.stats["conflicting_pairs"] == 1


def test_blank_method_becomes_unlabelled_and_designs_are_kept():
    result = flatten(load_rows())
    methods = dict(zip(result.designs["id"], result.designs["method"], strict=True))
    assert methods["a"] == "unlabelled"
    assert methods["b"] == "BindCraft"
    assert methods["d"] == "RFdiffusion"  # no binding evaluation, still a design


def test_binding_strength_none_is_kept_as_a_string():
    result = flatten(load_rows())
    row = outcome(result, "b")
    assert row["outcome"] == NON_BINDER
    assert row["binding_strength"] == "None"


def test_outcomes_are_per_target():
    result = flatten(load_rows())
    assert outcome(result, "b", "egfr")["outcome"] == BINDER


def test_non_numeric_scores_are_skipped_and_counted():
    result = flatten(load_rows())
    assert "esmfold_structure_prediction" not in result.scores["metric"].to_list()
    assert "flag" not in result.scores["metric"].to_list()
    assert result.stats["non_numeric_skipped"] == 2


def test_score_target_is_kept_and_may_be_absent():
    result = flatten(load_rows())
    a = result.scores.filter(pl.col("design_id") == "a")
    targets = dict(zip(a["metric"], a["target"], strict=True))
    assert targets["boltz2_iptm"] == "nipah-glycoprotein-g"
    assert targets["esmfold_plddt"] is None


def test_both_value_type_spellings_are_accepted_and_repeats_count_once():
    result = flatten(load_rows())
    e = result.scores.filter((pl.col("design_id") == "e") & (pl.col("metric") == "esmfold_plddt"))
    assert e.height == 1
    assert e["value"][0] == 90.0


def test_bad_rows_are_rejected_with_a_reason():
    result = flatten(load_rows())
    reasons = dict(zip(result.rejected["source_row"], result.rejected["reason"], strict=True))
    assert reasons == {6: "invalid evaluations JSON", 7: "missing id"}
    assert result.stats["rejected_rows"] == 2
    assert result.stats["designs"] == 5


def test_duplicate_ids_are_rejected():
    rows = load_rows()[:1] * 2
    result = flatten(rows)
    assert result.designs.height == 1
    assert result.rejected["reason"].to_list() == ["duplicate id"]


def test_identical_repeated_scores_count_once_and_are_not_conflicting():
    result = flatten([_row(("proteinmpnn_score", 1.5), ("proteinmpnn_score", 1.5))])
    row = _score(result, "proteinmpnn_score")
    assert row["conflicting"] is False
    assert row["value"] == 1.5
    assert result.stats["scores_averaged"] == 0


def _row(*evals):
    import json

    return {
        "id": "x",
        "name": "X",
        "sequence": "M",
        "author": "",
        "designMethod": "",
        "evaluations": json.dumps(
            [
                {"type": "computational", "metric": m, "value": v, "valueType": "numeric"}
                for m, v in evals
            ]
        ),
    }


def _score(result, metric):
    return next(r for r in result.scores.to_dicts() if r["metric"] == metric)


def test_esmfold_plddt_within_5_points_is_averaged():
    result = flatten([_row(("esmfold_plddt", 70.0), ("esmfold_plddt", 74.0))])
    row = _score(result, "esmfold_plddt")
    assert row["conflicting"] is False
    assert row["value"] == 72.0
    assert result.stats["scores_averaged"] == 1
    assert result.stats["score_conflicts"] == 0


def test_esmfold_plddt_exactly_5_points_apart_is_still_averaged():
    result = flatten([_row(("esmfold_plddt", 70.0), ("esmfold_plddt", 75.0))])
    assert _score(result, "esmfold_plddt")["value"] == 72.5


def test_esmfold_plddt_more_than_5_points_apart_is_conflicting():
    result = flatten([_row(("esmfold_plddt", 70.0), ("esmfold_plddt", 75.5))])
    row = _score(result, "esmfold_plddt")
    assert row["conflicting"] is True
    assert row["value"] is None
    assert result.stats["score_conflicts"] == 1


def test_esmfold_plddt_uses_the_full_spread_when_there_are_three_values():
    result = flatten(
        [_row(("esmfold_plddt", 70.0), ("esmfold_plddt", 72.0), ("esmfold_plddt", 77.0))]
    )
    assert _score(result, "esmfold_plddt")["conflicting"] is True


def test_other_scores_stay_conflicting_even_for_tiny_differences():
    result = flatten([_row(("proteinmpnn_score", 1.50), ("proteinmpnn_score", 1.51))])
    row = _score(result, "proteinmpnn_score")
    assert row["conflicting"] is True
    assert row["value"] is None
