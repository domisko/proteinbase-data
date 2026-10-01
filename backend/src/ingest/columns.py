"""Source-schema constants for the Proteinbase CSV snapshot (28 Jan 2026).

Verified against the downloaded file: 5,253 rows, UTF-8 with BOM. This is the only place source
names appear; see specs/001-binder-hit-rate-dashboard/data-model.md.
"""

CSV_ENCODING = "utf-8-sig"  # the file starts with a BOM

# Top-level CSV columns
COL_ID = "id"
COL_NAME = "name"
COL_SEQUENCE = "sequence"
COL_AUTHOR = "author"  # empty string when unknown
COL_METHOD = "designMethod"  # empty string when unlabelled (~2,200 rows)
COL_EVALUATIONS = "evaluations"  # JSON array of evaluation objects

UNLABELLED = "unlabelled"

# Keys inside each evaluation object. The data uses camelCase valueType; the docs page says
# value_type, so both are accepted.
EVAL_TYPE = "type"  # "computational" | "experimental"
EVAL_METRIC = "metric"
EVAL_TARGET = "target"  # present on some evaluations only
EVAL_VALUE = "value"
EVAL_VALUE_TYPE_KEYS = ("valueType", "value_type")

TYPE_COMPUTATIONAL = "computational"
TYPE_EXPERIMENTAL = "experimental"

# Experimental metrics
METRIC_BINDING = "binding"  # boolean; the binder / non-binder label (spec clarification)
METRIC_BINDING_STRENGTH = "binding_strength"  # "None" | "Weak" | "Medium" | "Strong" (strings)
METRIC_EXPRESSED = "expressed"  # boolean

# Scores where several recorded values are averaged when they agree closely (max - min <= the
# tolerance, in the metric's own units); a wider spread is treated as conflicting. Every other
# metric with differing repeated values is treated as conflicting. We do not know why the source
# records two ESMFold pLDDT values for most designs; see data-model.md.
AVERAGE_WITHIN = {"esmfold_plddt": 5.0}

# Targets are slugs in the data
TARGET_LABELS = {
    "nipah-glycoprotein-g": "Nipah glycoprotein G",
    "egfr": "EGFR",
}
MAIN_TARGETS = ("nipah-glycoprotein-g", "egfr")
