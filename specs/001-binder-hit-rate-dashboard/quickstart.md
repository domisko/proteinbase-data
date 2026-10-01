# Quickstart: Binder Hit-Rate Dashboard

Validation guide; see [data-model.md](data-model.md) and [contracts/openapi.yaml](contracts/openapi.yaml).

## Prerequisites
- Docker with Compose; Python 3.12 (for tests).
- The Proteinbase CSV snapshot (28 Jan 2026) downloaded per the README into `data/` (not committed).

## Run
1. `cp .env.example .env` and set `POSTGRES_PASSWORD`, then `docker compose up -d --build`
2. Ingest: `docker compose run --rm backend python -m src.ingest /data/<csv-file>`
   (the `data/` folder is mounted at `/data` inside the container)
   Expect: log lines with rows read (5,253), rejected, designs with outcomes, scores kept, non-numeric
   metrics skipped, binding conflicts and the snapshot checksum.
3. Open the frontend URL printed by Compose.

## Validate (maps to spec)
| Check | Expected |
|-------|----------|
| Pick Nipah glycoprotein G and EGFR | Method table with binders, labelled and no-result counts and hit rate (US1) |
| Compare a method's counts with a manual CSV count | Exact match (SC-002) |
| Sum of counts per target | Equals total designs for the target, incl. "unlabelled" (SC-003) |
| Pick a boltz2 score for Nipah | Missing count reflects designs lacking boltz2 metrics (US2, FR-005) |
| Methods with fewer than 20 tested designs | Marked "small sample" (FR-011) |
| Pick `esmfold_plddt` | Left-out counts shown for missing, conflicting and no-result designs (FR-005) |
| Pick a score | Binder and non-binder histograms on one scale, group sizes, missing count (US2) |
| Footer and `/meta` | Adaptyv Bio and Proteinbase credit, ODC-By, snapshot date 2026-01-28 (US3) |
| `git status` after ingest | No CSV tracked (FR-008) |
| Ingest log counts | ~9,300 binding evaluations collapse to 2,630 distinct pairs; 13 conflicting pairs logged as `no_result`; 4,627 score keys averaged (ESMFold pLDDT within 5 points) and 2,823 conflicting score keys excluded from distributions |
| Run ingest twice | Same numbers, no duplicate rows (FR-010) |

## Tests
`cd backend && pytest` — runs flattening and hit-rate unit tests (constitution III).
