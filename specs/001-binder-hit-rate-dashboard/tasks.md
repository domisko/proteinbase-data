---

description: "Task list for the Binder Hit-Rate Dashboard"
---

# Tasks: Binder Hit-Rate Dashboard

**Input**: Design documents from `/specs/001-binder-hit-rate-dashboard/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/openapi.yaml, research.md, quickstart.md

**Tests**: Required only for the data-flattening and hit-rate logic (constitution Principle III); no other test tasks are generated. Those tests are written alongside the logic they cover.

**Organization**: Grouped by user story so each can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 from spec.md
- Paths follow plan.md: `backend/src/`, `backend/tests/`, `frontend/src/` (existing: `backend/src/ingest/columns.py`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and structure

- [X] T001 Create the directory structure from plan.md: `backend/src/{ingest,core,db,api}`, `backend/tests/{fixtures,unit}`, `frontend/src/{components,pages,services}`, `data/`
- [X] T002 Create `backend/pyproject.toml` for Python 3.12 with pinned deps (fastapi, uvicorn, polars, psycopg[binary], pydantic, pytest, httpx) and a lockfile
- [X] T003 [P] Scaffold the Vite + React + TypeScript app in `frontend/` (package.json, tsconfig, vite config) with Recharts, and a committed lockfile
- [X] T004 [P] Create `docker-compose.yml` with `db` (PostgreSQL), `backend` and `frontend` services and Dockerfiles `backend/Dockerfile` and `frontend/Dockerfile`
- [X] T005 [P] Create `.gitignore` excluding `data/`, `*.csv`, `node_modules/`, `__pycache__/`, `.env`
- [X] T006 [P] Configure linting and formatting: ruff in `backend/pyproject.toml`, eslint and prettier in `frontend/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ingest pipeline, database and API skeleton that every user story needs

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Write the database schema for `snapshot`, `designs`, `outcomes`, `scores` and `rejected_rows` (with the indexes in data-model.md) in `backend/src/db/schema.sql` and a loader in `backend/src/db/connection.py`
- [X] T008 [P] Create small hand-made fixture CSVs in `backend/tests/fixtures/` (UTF-8 with BOM) covering: repeated identical binding evaluations, a conflicting pair, blank `designMethod`, a `binding_strength` of `"None"`, a boolean-valued and a JSON-valued computational metric, a score with and without `target`, invalid `evaluations` JSON and a missing `id`
- [X] T009 Implement `flatten()` in `backend/src/core/flatten.py` using `columns.py`: parse evaluations, produce design, outcome and score frames per the flattening rules in data-model.md (dedupe per (design, target); conflicts → `no_result`; skip non-numeric scores; blank method → `unlabelled`; reject rows without `id` or with invalid JSON) and return counts (evaluations read, distinct pairs, conflicts, skipped metrics, rejected rows)
- [X] T010 [P] Write unit tests for `flatten()` in `backend/tests/unit/test_flatten.py`, including: repeated identical binding evaluations count once, conflicting evaluations become `no_result`, blank method becomes `unlabelled`, non-numeric scores are skipped, `"None"` strength kept as a string, valueType and value_type both accepted
- [X] T011 Implement the ingest command `python -m src.ingest <csv>` in `backend/src/ingest/__main__.py`: read with `utf-8-sig`, compute sha256, call `flatten()`, load all tables in one transaction replacing any existing snapshot (idempotent), record snapshot metadata (date 2026-01-28, ODC-By, credit "Adaptyv Bio, Proteinbase"), and log the counts with basic logging
- [X] T012 Create the FastAPI app skeleton in `backend/src/api/main.py` with DB dependency, basic logging, CORS for the frontend, and a clear error response when no snapshot is loaded (message points to the README download instructions)
- [X] T013 [P] Create Pydantic response models matching `contracts/openapi.yaml` in `backend/src/api/models.py`
- [X] T014 [P] Create the typed API client skeleton and base URL config in `frontend/src/services/api.ts`

**Checkpoint**: Ingest loads the real CSV; the API starts.

---

## Phase 3: User Story 1 - Compare design methods for a target (Priority: P1) 🎯 MVP

**Goal**: Pick a target and see hit rate and counts per design method, with "unlabelled" included.

**Independent Test**: Select Nipah glycoprotein G and EGFR; each method row's counts and hit rate match a manual count of the CSV; counts sum to the target's design total (SC-002, SC-003).

- [X] T015 [P] [US1] Implement `hit_rates()` in `backend/src/core/hit_rate.py`: group a target's outcomes by method into binders, non_binders, no_result, labelled and hit_rate (null when labelled = 0), sorted by hit rate descending with nulls last, keeping `unlabelled` and zero-binder methods
- [X] T016 [P] [US1] Write unit tests for `hit_rates()` in `backend/tests/unit/test_hit_rate.py`: correct rates, `unlabelled` retained, zero-binder method shows 0%, all-`no_result` method has null rate, and the invariant that counts sum to the target's design total
- [X] T017 [US1] Add queries in `backend/src/db/queries.py` to list targets with design counts and to load a target's outcomes joined to designs as a Polars frame
- [X] T018 [US1] Implement `GET /targets` (slug, friendly name from `TARGET_LABELS`, design count; main targets first) and `GET /targets/{target}/hit-rates` (404 for unknown target) in `backend/src/api/routes_targets.py`, and register the router in `backend/src/api/main.py`
- [X] T019 [P] [US1] Build `TargetPicker` in `frontend/src/components/TargetPicker.tsx`, listing targets with counts, Nipah glycoprotein G and EGFR first
- [X] T020 [P] [US1] Build `HitRateTable` in `frontend/src/components/HitRateTable.tsx` showing method, binders, labelled, no-result and hit rate together, with "unlabelled" clearly labelled and a bar for the rate
- [X] T021 [US1] Build the `Dashboard` page in `frontend/src/pages/Dashboard.tsx` and mount it in `frontend/src/main.tsx`, wiring the target picker to the hit-rate table, with loading, empty and error states (including the no-snapshot message)

**Checkpoint**: US1 is fully usable and independently testable (MVP).

---

## Phase 4: User Story 2 - See which scores separate binders from non-binders (Priority: P2)

**Goal**: For the selected target, view a score's binder vs non-binder distribution with group sizes and exclusion counts.

**Independent Test**: For a target and score, two distributions appear on a shared scale with group sizes; the missing count matches designs lacking the score (e.g. boltz2 for Nipah).

- [X] T022 [P] [US2] Implement `distribution()` in `backend/src/core/distributions.py`: select scores with `target` equal to the selected target or null, bin both groups on shared edges, return group sizes, `missing_count` (binder / non-binder designs with no value) and `no_result_excluded`
- [X] T023 [P] [US2] Add queries in `backend/src/db/queries.py` to list a target's scores with `designs_with_value` and to load values plus outcomes for one target and metric
- [X] T024 [US2] Implement `GET /targets/{target}/scores` and `GET /targets/{target}/scores/{score}/distribution` (with `bins` query, 404s per contract) in `backend/src/api/routes_scores.py` and register the router in `backend/src/api/main.py`
- [X] T025 [P] [US2] Build `ScoreDistribution` in `frontend/src/components/ScoreDistribution.tsx`: score selector, overlaid binder and non-binder histograms on one axis, group sizes, and text stating the missing and no-result exclusion counts; show a clear message when a group is empty
- [X] T026 [US2] Add the score section to `frontend/src/pages/Dashboard.tsx`, resetting the score when the target changes

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 - Understand data source and licence (Priority: P3)

**Goal**: Credit, licence and snapshot date on every view; README explains the download.

**Independent Test**: Every page shows the credit, ODC-By and 28 Jan 2026; a fresh checkout's README explains where to get the CSV and the CSV is not tracked.

- [X] T027 [US3] Implement `GET /meta` (snapshot date, licence, credit, source file) in `backend/src/api/routes_meta.py` and register it in `backend/src/api/main.py`
- [X] T028 [P] [US3] Build `Attribution` in `frontend/src/components/Attribution.tsx` showing the credit to Adaptyv Bio and Proteinbase, the ODC-By licence and the snapshot date, and render it in the page layout in `frontend/src/pages/Dashboard.tsx` so it appears in every state including errors
- [X] T029 [P] [US3] Write `README.md`: purpose, where to download the Proteinbase CSV snapshot into `data/`, the ingest and run commands, the ODC-By licence and credit to Adaptyv Bio and Proteinbase, and a statement that the CSV is not committed

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T030 [P] Add a short API smoke test in `backend/tests/unit/test_api_smoke.py` checking `/meta`, `/targets` and one hit-rate response against fixture data
- [X] T031 Run the ingest twice against the real CSV and confirm the log shows 2,630 distinct pairs, 13 conflicts and identical results (FR-010) per `quickstart.md`
- [X] T032 Walk through every check in `quickstart.md` for Nipah glycoprotein G and EGFR, including the manual count comparison and SC-003 sum check, and record any deviation
- [X] T033 [P] Verify `git status` shows no CSV or `data/` content tracked and that `.gitignore` covers it (FR-008)
- [X] T034 [P] Check the layout at phone width and fix overflow in `frontend/src/pages/Dashboard.tsx`

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** → user stories → **Polish**.
- Foundational blocks all stories. T009 needs T008 fixtures for its tests (T010); T011 needs T007 and T009; T012 needs T007.
- **US1 (P1)** starts after Foundational. **US2 (P2)** and **US3 (P3)** depend only on Foundational; US2 reuses the Dashboard page created in T021, so T026 follows T021. T028 also edits `Dashboard.tsx`, so it follows T021 too.
- Within a story: core logic and tests → queries → routes → components → page wiring.
- T018, T024 and T027 all edit `backend/src/api/main.py`; do these registrations sequentially.

## Parallel Opportunities

- Setup: T003, T004, T005, T006 together after T001–T002.
- Foundational: T008, T013, T014 together; T010 alongside T011 once T009 is done.
- US1: T015 and T016, then T019 and T020 together.
- US2: T022 and T023 together, then T025.
- US3: T028 and T029 together.
- After Foundational, US1, US2 and US3 back-end tasks can be handled by different people.

## Implementation Strategy

- **MVP**: Phases 1, 2 and 3 (US1). Stop and validate against the manual CSV count before continuing.
- **Incremental**: add US2, then US3, validating each independently; finish with Polish.
- Out of scope (constitution VI): ordering, paid calls, structure viewers, accounts. Do not add tasks for them.

---

## Phase 7: Analysis follow-ups (2026-09-24)

- [X] T035 Docker hygiene (N1, N2): add `backend/.dockerignore` and `frontend/.dockerignore`, remove the unused root `.dockerignore`, stop publishing Postgres port 5432 and read the database password from a git-ignored `.env` (template `.env.example`) in `docker-compose.yml`
- [X] T036 Fix the quickstart ingest path to `/data/<csv-file>` and add the `.env` step in `specs/001-binder-hit-rate-dashboard/quickstart.md` (N3)
- [X] T037 Update `spec.md` wording for tested/no-result counts, both exclusion reasons in FR-005, target membership and repeated-value edge cases, and add FR-011 (F1–F3, N7)
- [X] T038 Replace score averaging with exclusion: `flatten()` keeps conflicting scores with a null value and `conflicting = true`; `distribution()`, queries, schema (version 2), API model, contract and UI report `conflicting_excluded`; update `data-model.md` and README (F3)
- [X] T039 Flag small samples: `small_sample` (fewer than 20 tested designs) on hit-rate rows and a small-sample note on distribution groups, with tests in `backend/tests/unit/` (N7)
- [X] T040 Remove the unused `KNOWN_SCORES` and `EVAL_UNIT` constants from `backend/src/ingest/columns.py` (N6)
- [X] T041 Average `esmfold_plddt` only when its repeated values differ by at most 5 points, otherwise mark the design conflicting; keep exclusion for every other score. Implemented via `AVERAGE_WITHIN` in `backend/src/ingest/columns.py` and `_build_scores()` in `backend/src/core/flatten.py`, with tests, and documented in `data-model.md`, `research.md` (R8), `spec.md` and README
