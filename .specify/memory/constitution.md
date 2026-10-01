<!--
Sync Impact Report
- Version change: 1.0.0 → 2.0.0
- Modified principles:
  - III. Test-First (NON-NEGOTIABLE) → III. Targeted Testing (relaxed: tests required only for
    data-flattening and hit-rate logic; test-first ordering no longer mandated)
  - V. Simplicity & Observability → V. Simplicity & Basic Logging (structured logging and
    per-stage record counts removed; basic logging only)
- Added sections: Principle VI. Small v1 Scope
- Removed sections: none
- Changed sections: Data & Technology Constraints (TODO(TECH_STACK) resolved; ODC-By attribution
  requirement added)
- Follow-up TODOs: none
-->
# proteinbase-data Constitution

## Core Principles

### I. Provenance & Reproducibility
Every dataset record MUST carry its source (origin, accession or identifier, retrieval date and
source version). Every derived dataset MUST be regenerable from raw inputs by a scripted,
version-controlled pipeline with pinned dependencies. Manual edits to derived data are prohibited.
Rationale: scientific data is only trustworthy if its origin and transformations can be audited.

### II. Schema-First Data Contracts
Every dataset and interface MUST have an explicit, versioned schema (types, units, allowed values,
nullability) defined before the code that produces it. Data MUST be validated against its schema
at pipeline boundaries, and invalid records MUST be rejected or quarantined, never silently
coerced. Rationale: explicit contracts catch corruption early and let consumers rely on structure.

### III. Targeted Testing
The data-flattening logic and the hit-rate logic MUST have automated tests, using small fixtures
of real records, and those tests MUST pass before merge. Tests for other code are encouraged but
not required. Rationale: these two computations produce the numbers users rely on, so silent
errors there are the costliest.

### IV. Immutable, Versioned Releases
Published dataset releases MUST be immutable and identified by a version. Changes ship as a new
release with a changelog; breaking schema changes require a MAJOR version increment. Raw
downloaded inputs MUST be preserved unmodified alongside checksums. Rationale: downstream users
and analyses must be able to cite and reproduce an exact release.

### V. Simplicity & Basic Logging
Start with the simplest tooling that works (YAGNI); every added dependency or abstraction MUST be
justified in the plan. Pipelines and the API MUST emit basic logging sufficient to diagnose
failures; no further observability requirements apply. Rationale: small systems are easier to
verify and maintain.

### VI. Small v1 Scope
v1 MUST stay small. Foundry API orders, structure viewers and paid calls are out of scope for v1
and MUST NOT be built, integrated or depended on. Adding any of them requires a constitution
amendment first. Rationale: a narrow scope keeps v1 deliverable and free of cost and ordering
risk.

## Data & Technology Constraints

- Technology stack: Python 3.12 and FastAPI for the backend, Polars for data processing,
  PostgreSQL run via Docker Compose for storage, and a TypeScript + React frontend. Deviations
  MUST be justified in the plan and reflected by amendment if they replace a listed component.
- Licensing and attribution: the data is licensed under ODC-By. All distributions, the UI and the
  documentation MUST credit Adaptyv Bio and Proteinbase as the data source. Source data licences
  MUST be recorded and respected.
- Identifiers: use stable, standard identifiers (e.g. UniProt, PDB) rather than internal ones
  where they exist.
- Secrets and credentials MUST NOT be committed to the repository.

## Development Workflow & Quality Gates

- Work proceeds through the Spec Kit flow: specify → plan → tasks → implement.
- A change MAY merge only when tests pass, schema validation passes and the plan's Constitution
  Check confirms compliance.
- Each pull request MUST state which principles it touches and justify any deviation.

## Governance

This constitution supersedes other project practices. Amendments MUST be documented in a pull
request that updates this file, includes a Sync Impact Report and, where existing work is affected,
a migration note. Versioning follows semantic versioning: MAJOR for removed or redefined
principles, MINOR for added principles or materially expanded guidance, PATCH for clarifications.
Compliance MUST be reviewed at every plan (Constitution Check) and pull request review;
unjustified complexity or violations block merge.

**Version**: 2.0.0 | **Ratified**: 2026-09-24 | **Last Amended**: 2026-09-24
