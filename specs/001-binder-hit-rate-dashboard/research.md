# Research: Binder Hit-Rate Dashboard

## R1. CSV column names and structure
- **Decision**: Use the verified schema in [data-model.md](data-model.md); all source names live
  in `backend/src/ingest/columns.py`. Read as `utf-8-sig`, parse the `evaluations` JSON per row,
  flatten to designs, outcomes and scores.
- **Rationale**: Facts come from the real snapshot (5,253 rows). One constants module keeps the
  flatten function testable.
- **Alternatives**: Auto-detect columns (fragile); wide table with one column per metric (targets
  and metrics vary per protein).
- **Status**: resolved; no open items.

## R2. Binder definition
- **Decision**: Use the boolean experimental `binding` evaluation per (design, target) as the
  binder / non-binder label; non-boolean or conflicting values become `no_result` (spec
  clarification 2026-09-24). `binding_strength` is kept as extra detail, not used to define binders.
- **Rationale**: Avoids inventing a strength cutoff; counts stay checkable against source.

## R3. Where hit-rate is computed
- **Decision**: Load a target's designs from Postgres into a Polars frame and compute hit rates
  and distributions in pure Python functions.
- **Rationale**: Data is small; keeps the logic in one testable place instead of duplicated in SQL.
- **Alternatives**: SQL aggregation (needs a database in tests); precomputed tables (stale risk).

## R4. Score distributions
- **Decision**: Backend returns per-group histogram bins on a shared bin scale, plus group sizes
  and missing-value count. Frontend draws overlaid bars.
- **Rationale**: Same scale for both groups (spec US2); small payload.
- **Alternatives**: Return raw values (larger, pushes logic to the client).

## R5. Storage layout
- **Decision**: Separate `designs`, `outcomes` (per design and target) and long-format `scores`
  tables; only numeric computational metrics are kept, JSON-valued ones are skipped in v1.
- **Rationale**: New score columns need no schema change.
- **Alternatives**: One wide table (schema churn per score).

## R6. Charts and frontend tooling
- **Decision**: Vite + React + TypeScript with Recharts.
- **Rationale**: Minimal setup, sufficient for tables, bar charts and histograms.

## R7. Running and data delivery
- **Decision**: Docker Compose runs Postgres, backend and frontend; the ingest command runs
  against a CSV in the gitignored `data/` folder.
- **Rationale**: Meets constitution stack; keeps raw CSV out of git (FR-008).

## R8. Repeated scores with different values
- **Decision**: Identical repeats count once. For `esmfold_plddt` only, average the values when
  they differ by at most 5 points, otherwise mark the design conflicting and exclude it from
  distributions (counted and shown). All other scores: any difference means conflicting.
- **Rationale**: Nearly all designs (4,934 of 5,253) carry two or more different ESMFold pLDDT
  values. Median gap is 0.35 points and only 307 designs exceed 5, so averaging close values keeps
  the metric usable while excluding the ambiguous ones. We do not know why the source records
  several values, so we avoid guessing beyond this small tolerance.
- **Alternatives**: exclude every differing design (leaves ~4% of Nipah designs, useless); keep
  the first value (depends on row order); average everything (hides gaps up to 30 points).
- **Open question**: the meaning of the repeated ESMFold values; ask the data provider if it
  matters.

