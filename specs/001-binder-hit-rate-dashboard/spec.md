# Feature Specification: Binder Hit-Rate Dashboard

**Feature Branch**: `001-binder-hit-rate-dashboard`

**Created**: 2026-09-24

**Status**: Draft

**Input**: User description: "A small public dashboard built on the open Proteinbase dataset (CSV snapshot 28 Jan 2026, ODC-By license, credit Adaptyv Bio). It answers: for a chosen target (mainly Nipah glycoprotein G and EGFR), which protein design methods produce the most binders, and which computational scores (for example Boltz-2 or ESMFold metrics) separate binders from non-binders. Users pick a target, see hit rate by design method (with counts), and see score distributions for binders versus non-binders. Proteins with no design method label are shown as \"unlabelled\" and not dropped silently. The raw CSV is not committed; the README explains where to download it and credits the source. Out of scope: ordering experiments, any paid API call, structure viewers, user accounts."

## Clarifications

### Session 2026-09-24

- Q: How should a design be classed as a "binder" when its result is inconclusive, weak or not clearly recorded? → A: Use the dataset's own binder / non-binder label as given; designs with no clear label are excluded from hit rate but counted and shown as "no result".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare design methods for a target (Priority: P1)

A protein designer opens the dashboard, picks a target (for example Nipah glycoprotein G or EGFR),
and sees, for each design method, how many designs have a clear result ("tested"), how many were
binders and the resulting hit rate, plus how many have no result. This tells them which methods are worth using for that target.

**Why this priority**: This is the core question the dashboard exists to answer and is a usable MVP
on its own.

**Independent Test**: Select a target and check that each method row shows tested (clear-result)
count, binder count, no-result count and hit rate matching a manual count of the source data for that target.

**Acceptance Scenarios**:

1. **Given** the dashboard is loaded, **When** the user selects a target, **Then** a table or
   chart lists every design method present for that target with tested (clear-result) count, binder
   count, no-result count and hit rate.
2. **Given** a target is selected, **When** the results are shown, **Then** methods are ordered so
   the highest hit rate is easy to identify, and counts are visible alongside every rate.
3. **Given** some proteins for the target have no design method label, **When** results are shown,
   **Then** they appear as an "unlabelled" group with their own counts and hit rate.

---

### User Story 2 - See which scores separate binders from non-binders (Priority: P2)

For the selected target, the user views the distribution of each available computational score
(for example Boltz-2 or ESMFold metrics) split into binders versus non-binders, to judge which
scores are useful for filtering designs before testing.

**Why this priority**: It answers the second key question, but depends on the target selection
from Story 1.

**Independent Test**: Select a target and a score and verify that two distributions (binders,
non-binders) are shown, with counts matching the source data.

**Acceptance Scenarios**:

1. **Given** a target is selected, **When** the user chooses a score, **Then** the binder and
   non-binder distributions are shown side by side on the same scale, with the number of proteins
   in each group.
2. **Given** some proteins have no value for the chosen score, **When** the distribution is shown,
   **Then** the number of proteins excluded for missing values is stated.
3. **Given** some proteins have several different recorded values for the chosen score, **When**
   the distribution is shown, **Then** those proteins are left out and their number is stated.

---

### User Story 3 - Understand data source and licence (Priority: P3)

A visitor can see where the data comes from, its snapshot date and licence, and credit to Adaptyv
Bio and Proteinbase; a developer reading the README learns where to download the raw CSV.

**Why this priority**: Required for licence compliance but does not affect the analysis itself.

**Independent Test**: Open the dashboard and README and confirm the credit, licence, snapshot date
and download instructions are present.

**Acceptance Scenarios**:

1. **Given** any dashboard page, **When** the user views it, **Then** attribution to Adaptyv Bio
   and Proteinbase, the ODC-By licence and the snapshot date (28 Jan 2026) are visible.
2. **Given** a fresh checkout, **When** a developer reads the README, **Then** it explains where
   to download the raw CSV and credits the source; the CSV itself is not in the repository.

---

### Edge Cases

- A method has fewer than 20 designs with a clear result: it is flagged as a small sample, and
  rates are never shown without their counts.
- A design has no clear binder / non-binder label: it is excluded from hit rate but counted and
  shown as "no result" for its method.
- A method has zero binders: it is still listed with a 0% hit rate.
- A target has no binders or no non-binders: the distribution view states this instead of showing
  an empty or misleading chart.
- The raw CSV is missing when the application is set up: a clear message explains where to
  download it.
- Design method labels differ only by spelling or case: they are treated as the same method only
  if the source data does so; otherwise they are shown as given.
- A protein has several binding results for the same target: identical repeats count once; if they
  disagree the protein is shown as "no result" for that target.
- A protein has several different recorded values for the same score: it is excluded from that
  score's distributions and counted, instead of guessing a value. The one exception is ESMFold
  pLDDT, where values that agree within 5 points are averaged; a wider gap counts as conflicting.
- Proteins with no design method label are never dropped: they appear as "unlabelled".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to select a target from the targets present in the dataset, with
  Nipah glycoprotein G and EGFR easy to find.
- **FR-002**: For the selected target, the system MUST show hit rate by design method, where hit
  rate is binders divided by designs with a clear binder or non-binder label, together with binder,
  labelled-tested and "no result" counts. Binder status is the dataset's own label, not a
  dashboard-defined cutoff.
- **FR-003**: The system MUST show proteins with no design method label as a group named
  "unlabelled" and MUST NOT silently exclude them from any count or rate.
- **FR-004**: For the selected target, users MUST be able to choose a computational score and see
  its distribution for binders versus non-binders, with group sizes.
- **FR-005**: The system MUST state how many proteins were left out of a distribution, separately
  for each reason: the score value is missing; the source records several different values for
  the score (conflicting); or the protein has no clear binder / non-binder result.
- **FR-006**: The dashboard MUST be publicly viewable without an account or sign-in.
- **FR-007**: Every dashboard view MUST display credit to Adaptyv Bio and Proteinbase, the ODC-By
  licence and the data snapshot date.
- **FR-008**: The raw source CSV MUST NOT be committed to the repository; the README MUST explain
  where to download it and MUST credit the source.
- **FR-009**: The system MUST NOT provide experiment ordering, make any paid call, include
  structure viewers or offer user accounts.
- **FR-010**: Hit-rate and score-grouping results MUST be reproducible from the source CSV
  snapshot, so the same input always yields the same numbers.
- **FR-011**: Any group (a design method in the hit-rate view, or the binder / non-binder group in a
  distribution) with fewer than 20 designs MUST be flagged as a small sample.

### Key Entities

- **Target**: A protein a design was tested against (for example Nipah glycoprotein G, EGFR).
- **Design**: A tested protein design, linked to one target, with an optional design method label,
  a binder or non-binder outcome and a set of computational scores.
- **Design Method**: The approach used to create a design; may be absent, shown as "unlabelled".
- **Score**: A named computational metric (for example Boltz-2 or ESMFold metrics) with a numeric
  value per design, possibly missing.
- **Hit Rate**: For a target and method, binders divided by designs with a clear binder / non-binder label,
  reported with counts (designs without a clear label are counted separately as "no result").

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can select a target and read the hit rate and counts per design method in
  under 30 seconds from opening the dashboard.
- **SC-002**: For Nipah glycoprotein G and EGFR, hit rates and counts shown match an independent
  manual count of the source snapshot in 100% of methods checked.
- **SC-003**: Across all targets, the sum of per-method counts (including "unlabelled" and
  "no result") equals the total designs for that target, so no protein is dropped.
- **SC-004**: For any selected target and score, a user can see binder versus non-binder
  distributions in under 5 seconds after choosing.
- **SC-005**: 100% of dashboard views show the required credit, licence and snapshot date.
- **SC-006**: A developer with no prior knowledge can locate the CSV download instructions in the
  README and have the dashboard running with data within 15 minutes.

## Assumptions

- The dashboard is read-only and uses a single fixed data snapshot (28 Jan 2026); updating to a
  newer snapshot is a separate task.
- A "binder" is defined by the binder / non-binder label recorded in the source data; the
  dashboard does not redefine it or apply its own strength cutoff.
- Nipah glycoprotein G and EGFR are the main targets, but any target in the data can be selected.
- Available scores are the numeric computational metrics in the source data; a score that names a
  target applies only to that target, and other (JSON, text, boolean) metrics are not shown.
- The source records several ESMFold pLDDT values for most proteins and it is not known why; the
  5-point averaging rule is a pragmatic choice (see data-model.md).
- A protein belongs to a target only if the source has a binding result for that protein and
  target; proteins with no binding result for a target are not counted for it.
- Users have a modern desktop or mobile web browser and an internet connection.
- The source data is not redistributed in the repository; each deployment obtains it from the
  original publisher under ODC-By.
