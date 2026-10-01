# Data Model: Binder Hit-Rate Dashboard

Verified against the 28 Jan 2026 snapshot (5,253 rows, UTF-8 with BOM). Source names live in
[backend/src/ingest/columns.py](../../backend/src/ingest/columns.py).

## Source format

- Top-level columns: `id`, `name`, `sequence`, `author`, `designMethod`, `evaluations`.
- Read the file as `utf-8-sig`. Empty `designMethod` (~2,200 rows) and empty `author` are empty
  strings, not nulls.
- `evaluations` is a JSON array. Each object has `type` (`computational` | `experimental`),
  `metric`, `value`, `valueType` (camelCase in the data; `value_type` per the docs, accept both),
  optional `target` and optional `unit`.
- Experimental metrics: `binding` (boolean), `binding_strength` (string `"None"`, `"Weak"`,
  `"Medium"`, `"Strong"`; `"None"` is a string, not null), `expressed` (boolean). A protein can
  have several `binding` evaluations, one per target.
- Targets are slugs: `nipah-glycoprotein-g` (most data), `egfr`, then many with very little data
  (`mdm2`, `pd-l1`, `human-tnfa`, ...).
- Numeric computational metrics include `esmfold_plddt`, `proteinmpnn_score`, `molecular_weight`,
  `isoelectric_point`, `boltz2_iptm`, `boltz2_ptm`, `boltz2_plddt`, `boltz2_ipsae`,
  `boltz2_pdockq`. About 3,800 of 5,253 proteins have the boltz2 metrics.
- JSON-valued metrics (structure predictions, images, `pae_file`) are skipped in v1.

## Flattening rules (`core/flatten.py`)

1. Parse `evaluations`; if it is not valid JSON, reject the row (`rejected_rows`).
2. **Design**: one row per CSV row. Blank `designMethod` becomes `unlabelled`; blank `author`
   is stored as null.
3. **Outcome** (exactly one per design and target): from experimental `binding` evaluations with
   a `target`. The snapshot has about 9,300 such evaluations but only 2,630 distinct
   (design, target) pairs, so evaluations MUST be deduplicated per pair before counting.
   Per pair: `true` → `binder`, `false` → `non_binder`, any other value → `no_result`. Repeated
   evaluations with the same value count once. Pairs whose evaluations conflict (13 in this
   snapshot) become `no_result` and are logged. A design belongs to a target only if it has a
   `binding` evaluation for it.
4. **Binding strength**: the `binding_strength` label for the same design and target is stored as
   extra detail (`"None"` kept as the string). `binding` is authoritative for binder status; a
   mismatch (for example `binding` false with strength `Strong`) is logged, not corrected.
5. **Scores**: keep computational evaluations whose `value` is a JSON number (not boolean). Skip
   all others (strings, objects, arrays) and count them in the ingest log. Store the evaluation's
   `target` when present, else null (numeric scores occur both with and without a target in the
   data). Identical repeated score evaluations for the same (design, metric, target) count once. Repeats
   with different values are resolved per metric (`AVERAGE_WITHIN` in `columns.py`):
   - **`esmfold_plddt`**: almost every design has two or more recorded values (4,934 of 5,253
     differ). If the values differ by at most **5 points** (max minus min, so exactly 5 is
     accepted) the design's value is their **mean**; if they differ by more than 5 points the
     design is **conflicting** (307 designs in this snapshot). Measured over all 4,934 designs
     with differing values: median gap 0.35, mean 1.32, maximum 30.59 points.
   - **every other metric**: any difference makes the design conflicting.
   A conflicting row keeps a null `value` and `conflicting = true`, so the design is left out of
   that score's distributions and counted (`conflicting_excluded`); the ingest log reports
   `scores_averaged` (4,627 keys) and `score_conflicts` (2,823 keys) for this snapshot.
   **We do not know why the source records two (sometimes up to five) ESMFold pLDDT values per
   design** (for example, separate folding runs, different sequences such as a redesign, or
   duplicated submissions); nothing in the data distinguishes them. The 5-point rule is a
   pragmatic choice, not a scientific one: the averaged value should be read as approximate.
6. `expressed` and other experimental metrics are not used in v1.

## Tables

### snapshot
| Field | Type | Notes |
|-------|------|-------|
| id | integer PK | one row per ingested snapshot |
| source_file | text | original CSV file name |
| snapshot_date | date | 2026-01-28 |
| sha256 | text | checksum of the raw CSV |
| licence | text | "ODC-By" |
| credit | text | "Adaptyv Bio, Proteinbase" |
| ingested_at | timestamptz | |

### designs
| Field | Type | Notes |
|-------|------|-------|
| id | text PK | source `id` |
| snapshot_id | integer FK | provenance |
| source_row | integer | 1-based row number in the CSV |
| name | text | source `name` |
| sequence | text | source `sequence` |
| author | text, nullable | null when blank |
| method | text | `designMethod`, or `unlabelled` |

### outcomes
| Field | Type | Notes |
|-------|------|-------|
| design_id | text FK | |
| target | text, indexed | slug, e.g. `nipah-glycoprotein-g` |
| outcome | enum | `binder`, `non_binder`, `no_result` |
| binding_strength | text, nullable | `None`, `Weak`, `Medium`, `Strong` as strings |

Primary key: (design_id, target).

### scores
| Field | Type | Notes |
|-------|------|-------|
| design_id | text FK | |
| metric | text | e.g. `boltz2_iptm`, `esmfold_plddt` |
| target | text, nullable | set when the evaluation names a target |
| value | double, nullable | null when `conflicting`; a missing score has no row |
| conflicting | boolean | true when the source gave several different values for this key |

Unique on (design_id, metric, target); index on (metric).

### rejected_rows
| Field | Type | Notes |
|-------|------|-------|
| snapshot_id | integer FK | |
| source_row | integer | |
| reason | text | e.g. missing id, invalid evaluations JSON |

## Validation rules
- `id` is required; a missing `id` or invalid `evaluations` JSON sends the row to `rejected_rows`
  and the count is logged.
- Outcomes are unique per (design, target); the ingest log reports evaluations read, distinct
  pairs (expected 2,630 for this snapshot) and conflicting pairs (expected 13).
- Rows with no `binding` evaluation still load as designs (they simply belong to no target).
- Ingest replaces a snapshot in one transaction (idempotent).

## Target labels
Slugs are shown with friendly names for the main targets (`nipah-glycoprotein-g` → "Nipah
glycoprotein G", `egfr` → "EGFR"); other targets show their slug. Targets with very few designs
are listed with their counts so small samples are visible.

## Derived results (not stored)
- **HitRate row** (target, method): `binders`, `non_binders`, `no_result`,
  `labelled = binders + non_binders`, `hit_rate = binders / labelled` (null when labelled = 0).
  Invariant: binders + non_binders + no_result = designs with an outcome for that target and
  method; summed over methods (incl. `unlabelled`) it equals the target's design count (SC-003).
- **Small sample**: a hit-rate row with `labelled < 20`, or a distribution group with `n < 20`.
- **Distribution** (target, metric): scores used are those with `target` equal to the selected
  target, or null when the metric has no target. Shared bin edges; per-group counts for `binder`
  and `non_binder`; group sizes; `no_result_excluded` (designs of the target with outcome
  `no_result`); `conflicting_excluded` (binder / non-binder designs whose value for the metric is
  conflicting); `missing_count` (binder / non-binder designs with no record of the metric at all,
  e.g. those lacking boltz2 metrics).
