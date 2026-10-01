# Implementation Plan: Binder Hit-Rate Dashboard

**Branch**: `001-binder-hit-rate-dashboard` | **Date**: 2026-09-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-binder-hit-rate-dashboard/spec.md`

## Summary

A read-only public dashboard over the Proteinbase CSV snapshot (28 Jan 2026). A scripted ingest
step flattens the CSV (design rows plus a JSON `evaluations` column) with Polars into PostgreSQL
tables for designs, per-target outcomes and numeric scores. A small FastAPI
backend serves targets, hit rate by design method and binder vs non-binder score distributions. A
React + TypeScript frontend renders a target picker, a method hit-rate table/chart and a score
distribution chart, and shows the ODC-By credit on every view. Hit-rate and flattening logic live
in pure Polars functions so they are unit-testable without a database.

## Technical Context

**Language/Version**: Python 3.12 (backend, ingest); TypeScript 5 (frontend)

**Primary Dependencies**: FastAPI, Polars, psycopg 3 (Postgres driver), Pydantic; React, Vite,
Recharts (charts)

**Storage**: PostgreSQL via Docker Compose; raw CSV kept outside the repo and gitignored

**Testing**: pytest for flattening and hit-rate logic (required by constitution III), including: repeated
identical binding evaluations count once, conflicting evaluations become `no_result`, blank method
becomes `unlabelled`, non-numeric scores are skipped; a small
smoke test for the API; no frontend test suite required in v1

**Target Platform**: Linux containers (Docker Compose); modern desktop and mobile browsers

**Project Type**: web application (backend + frontend)

**Performance Goals**: target selection to rendered result under 5 s (SC-004); data volume is
thousands of rows, so no optimisation beyond an index on target

**Constraints**: no auth, no paid calls, no structure viewer, no ordering (Principle VI); ingest
must be reproducible from the CSV (Principle I); basic logging only (Principle V)

**Scale/Scope**: one static snapshot of 5,253 designs; 2 main targets (Nipah glycoprotein G, EGFR) plus many sparse ones; 3 views

## Constitution Check

| Principle | Status | Note |
|-----------|--------|------|
| I. Provenance & Reproducibility | Pass | Every design keeps its source row number and snapshot (file name, date, checksum); ingest is a scripted, idempotent command; dependencies pinned via lockfiles. |
| II. Schema-First Data Contracts | Pass | Column mapping and Pydantic/DB schema defined in [data-model.md](data-model.md) and [contracts/](contracts/) before code; invalid rows quarantined and counted. |
| III. Targeted Testing | Pass | pytest covers `flatten` and `hit_rates` with small fixtures. |
| IV. Immutable, Versioned Releases | Pass | Snapshot is identified by date; ingest replaces the whole snapshot atomically; raw CSV checksum recorded. Nothing is redistributed. |
| V. Simplicity & Basic Logging | Pass | Four small tables, five endpoints, no cache, no queue. |
| VI. Small v1 Scope | Pass | No ordering, paid calls, viewers or accounts. |
| Constraints: stack, ODC-By credit | Pass | Stack as mandated; credit shown in UI footer, API `/meta` and README. |

Post-design re-check: no violations; Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-binder-hit-rate-dashboard/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md             # created by /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── ingest/          # CSV -> flatten -> Postgres (CLI entry point)
│   ├── core/            # pure Polars logic: flatten.py, hit_rate.py, distributions.py
│   ├── db/              # schema and queries
│   └── api/             # FastAPI app, routes, response models
└── tests/
    ├── fixtures/        # tiny hand-made CSV samples
    └── unit/            # flatten and hit-rate tests

frontend/
└── src/
    ├── components/      # TargetPicker, HitRateTable, ScoreDistribution, Attribution
    ├── pages/           # Dashboard
    └── services/        # API client

data/                    # gitignored; user places the downloaded CSV here
docker-compose.yml       # postgres, backend, frontend
README.md                # download instructions, credit, licence
```

**Structure Decision**: Web application layout (backend + frontend) matching the mandated stack.
Core computations sit in `backend/src/core` with no database or web imports so they can be tested
in isolation.

## Complexity Tracking

No violations to justify.
