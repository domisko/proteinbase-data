"""Regenerate sample.csv: a tiny hand-made CSV (UTF-8 with BOM) shaped like the real snapshot."""

import csv
import json
from pathlib import Path

T = "nipah-glycoprotein-g"


def ev(kind, metric, value, value_type, target=None):
    e = {"type": kind, "metric": metric, "value": value, "valueType": value_type}
    if target:
        e["target"] = target
    return e


def binding(value, target=T):
    return ev("experimental", "binding", value, "boolean", target)


def strength(value, target=T):
    return ev("experimental", "binding_strength", value, "label", target)


ROWS = [
    # a: repeated identical binding evaluations (3x true) -> one binder; blank method
    (
        "a",
        "A",
        "MKV",
        "",
        "",
        [
            binding(True),
            binding(True),
            binding(True),
            strength("Strong"),
            ev("computational", "esmfold_plddt", 80.0, "numeric"),
            ev("computational", "boltz2_iptm", 0.9, "numeric", T),
            ev("computational", "esmfold_structure_prediction", {"x": 1}, "json"),
        ],
    ),
    # b: non-binder with strength "None" (a string), also has an egfr binder result
    (
        "b",
        "B",
        "MKL",
        "Lab",
        "BindCraft",
        [
            binding(False),
            strength("None"),
            binding(True, "egfr"),
            ev("computational", "esmfold_plddt", 60.0, "numeric"),
            ev("computational", "boltz2_iptm", 0.2, "numeric", T),
        ],
    ),
    # c: conflicting binding evaluations -> no_result
    (
        "c",
        "C",
        "MKI",
        "",
        "BindCraft",
        [binding(True), binding(False), ev("computational", "esmfold_plddt", 70.0, "numeric")],
    ),
    # d: no binding evaluation at all -> a design but in no target; boolean score is skipped
    ("d", "D", "MKA", "", "RFdiffusion", [ev("computational", "flag", True, "boolean")]),
    # e: value_type spelling from the docs; same score with and without a target
    (
        "e",
        "E",
        "MKG",
        "",
        "RFdiffusion",
        [
            binding(True),
            strength("Weak"),
            {
                "type": "computational",
                "metric": "esmfold_plddt",
                "value": 90,
                "value_type": "numeric",
            },
            ev("computational", "esmfold_plddt", 90.0, "numeric"),
        ],
    ),
    # f: invalid evaluations JSON -> rejected (written raw below)
    ("f", "F", "MKQ", "", "", "not json"),
    # missing id -> rejected
    ("", "G", "MKW", "", "", []),
]

out = Path(__file__).with_name("sample.csv")
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["id", "name", "sequence", "author", "designMethod", "evaluations"])
    for design_id, name, seq, author, method, evals in ROWS:
        raw = evals if isinstance(evals, str) else json.dumps(evals)
        writer.writerow([design_id, name, seq, author, method, raw])
