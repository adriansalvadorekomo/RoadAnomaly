# Feature Specification: RoadAnomaly dataset audit MVP

**Feature Branch**: `docs/adopt-sdd` (SDD integration branch)
**Feature Directory**: `specs/003-dataset-understanding`
**Created**: 2026-10-22
**Status**: Draft

**Input**: Define a read-only, reproducible dataset audit for the 60-frame RoadAnomaly
benchmark. The MVP produces one schema-validated JSON summary and one Markdown report derived
from it. Visual overlays, aggregate figures, the visual-review ledger and the normal-road
readiness gate are documented post-MVP extensions, not acceptance blockers.

## Context

The repository contains the 60 RoadAnomaly benchmark frames under `data/frames/` and no
normal-road corpus. The accepted Stage 2 audit is the evidence baseline. It computed inventory,
coverage, annotation, provenance and leakage findings from local files, but it did not visually
verify registration.

This feature builds the smallest defensible audit that:

- reproduces the accepted Stage 2 baseline without fitting or scoring a model;
- makes the JSON summary the single machine-readable evidence source;
- renders the Markdown report only from a schema-valid JSON summary;
- reports fingerprint drift, corrupt inputs and annotation invariant failures explicitly;
- leaves visual review, figures and normal-road readiness as separate extensions.

P0-1 (class names, IDs and ignore list), P0-2 (metric placement), P0-3 (benchmark scoring) and
P0-4 (threshold protocol) remain open. This feature does not resolve them.

## Scope

| Deliverable | MVP? | Output |
|---|---|---|
| Core benchmark audit | Yes | `docs/validation/roadanomaly-eda.json` and `roadanomaly-eda.md` |
| Fingerprint, inventory, coverage, scale, mapping, ROI, credits, provenance | Yes | Fields in the JSON summary and report |
| Visual overlays and review ledger | No | Post-MVP extension; see `contracts/visual-review-ledger.md` |
| Aggregate figures | No | Post-MVP extension |
| Normal-road readiness gate | No | Post-MVP extension; see `contracts/normal-road-readiness.md` |

The MVP has no `.audit-staging/`, journal, backup, output-manifest or readiness state in the
canonical JSON schema.

## Approved decisions

- The JSON summary is authoritative. The Markdown report is a deterministic view of the
  validated JSON bytes and records the SHA-256 of that JSON.
- The JSON does not contain the report hash. This one-way orientation avoids a circular digest.
- A fingerprint mismatch is a hard failure: exit `2`, print the historical and computed values
  and counts, and write no canonical output. It never replaces the historical baseline.
- An instance/semantic mismatch is a hard failure: exit `2`, print every affected frame with
  extra/missing pixel counts, and write no canonical output.
- The MVP writes only two canonical files under the configured output root, plus transient
  temporary siblings. It does not create figures, overlays, directories below the output root, a
  review ledger or a readiness report.
- A normal failure before publication leaves the previous JSON/report pair unchanged. The two
  final file replacements are individually atomic, not set-atomic; a crash or replacement failure
  between them can leave a mixed pair. The JSON remains authoritative and check mode detects the
  mismatch. No journal or rollback machinery is added for this narrow case.
- Visual review, advanced figures and readiness are extensions. They must not block or weaken
  the core audit.
- No existing scientific invariant, public model contract or ADR is changed.

## Accepted Stage 2 baseline

These values are the regression target for the MVP. They are not new evidence produced by this
specification.

| Area | Accepted local value | Evidence class | Note |
|---|---|---|---|
| Historical local fingerprint | `7c16ab39607d68a66bc2f4ac321933f64221d62980119ea780af5abf2a99f4e2` over 677 files and 13,135,474 bytes | computed_local | Exact byte encoding documented below; local reconstruction matches |
| Images | 60 WebP frames, 1280 × 720, RGB | computed_local | One frame-list entry per frame |
| Annotations | 60 label directories; 46 with instance annotations; 14 semantic-only; 201 instances, all `cls=2` | computed_local | Semantic values `{0,2}` only |
| Instance/semantic consistency | 46/46 exact; 0 extra instance pixels; 0 missing instance pixels; 14 semantic-only excluded | computed_local | Union of instance values `1..N` equals semantic value `2` |
| Coverage | 9.849561 % pooled; 0.374674–42.328559 % per frame; median 6.622938 %; six frames below 1 % | computed_local | Six-decimal serialization |
| Categories | animals 31, obstacles 15, cones 8, lost_tires 3, vehicle 3 | computed_local | Filename-prefix object categories, not scene IDs |
| Object scale | 35/201 ROIs with area < 1024 px²; 20/201 with both dimensions < 32 px; 46/201 with either; 86.7 px median ROI equivalent square; 85 × 107 px median ROI bounding box; 51.2 px median mask-pixel equivalent square | computed_local | Definitions must accompany values |
| Instance mapping | Mask values contiguous `1..N` in all 46 frames; value `k` equals the k-th `instances` entry in 35/46 frames; differs in 11/46 | computed_local | Existing test only asserts `max(mask) == len(instances)` |
| ROI bounds | 11/201 ROIs extend outside 1280 × 720; 17/201 instance pixel boxes are non-tight under the order mapping; 201/201 centroids are inside | computed_local | No silent clipping |
| Duplicates | No exact or decoded-pixel duplicate frames; no dHash-close pairs at distance ≤ 6 | computed_local | Method-limited, not a proof of no near-duplicates |
| Credits | 60 frames have credit entries; 24 lack explicit per-image licence tokens; one four-frame group lacks a URL; 13 frames fall into four source groups | computed_local | Source groups are attribution groups, not scenes |
| Upstream provenance | Local citation is Lis et al., ICCV 2019; no release/version/checksum identifier | upstream_unverified | Do not invent a release identifier |
| Normal-road corpus | Absent; no manifest, class map, scene list or split | computed_local | G10 remains open |
| Visual registration | Not verified | unresolved | Not assessed in the MVP |

## Documented claims that must not be silently reconciled

| Documented claim | Local evidence | Required treatment |
|---|---|---|
| `labels_instance.png` pixel value equals the instance ID | 11/46 frames disagree under the k-th-entry mapping | Report both; do not edit labels or declare one interpretation canonical |
| Median instance is “87 × 87” and 35/201 are “smaller than 32 × 32” | 35/201 under ROI area < 1024; 20/201 under both-dimensions < 32; 46/201 under either | Report each definition; do not repeat one number as the only truth |
| Filename prefixes are a “natural scene grouping” | No scene IDs or source scene metadata exist locally | Treat prefixes as object categories only; report the documentation gap |
| Per-image terms are recorded in `credits.txt` | 24 frames lack explicit licence tokens; one group lacks a URL | Classify as unresolved; local attribution is not redistribution proof |
| Benchmark scene-prefix folds can be used for threshold tuning | No benchmark scene identities exist locally | Report the gap; do not create folds or a split hash |
| Coverage is “9.8 %” | Exact value is 9.849561 % | Preserve both values and the rounding rule |

## Historical fingerprint recipe

The historical value `7c16ab39607d68a66bc2f4ac321933f64221d62980119ea780af5abf2a99f4e2` is
the accepted baseline. Its exact byte encoding is:

1. Enumerate every regular file under `data/` recursively; do not follow symlinks.
2. Sort by path relative to `data/`, using POSIX separators and byte order.
3. Initialize SHA-256.
4. For each file, update with the UTF-8 relative path, one NUL byte (`\0`), and the raw 32-byte
   SHA-256 digest of the file content.
5. Do not append a trailing NUL or newline.
6. Hex-encode the final digest.

The audit keeps the historical hash and the historical counts `677` and `13,135,474` as fixed
baseline constants, computes current counts separately, and compares the computed hash with the
historical value. The report must state that the byte layout is a local reconstruction, not the
recovered original Stage 2 implementation.

## Terminology

- **Computed finding**: a value produced by the audit from local files.
- **Documented claim**: a statement in `docs/dataset.md`, `README.md` or `data/readme.md` that
  was not recomputed.
- **Upstream-unverified claim**: a claim requiring the original release, publisher metadata or
  external licence terms not locally present.
- **Historical fingerprint**: the accepted Stage 2 value, its construction and exact encoding.
- **Instance/semantic invariant**: for every instance-annotated frame, the union of instance
  values `1..N` equals the semantic anomaly pixels (value `2`).
- **Source group**: an attribution-derived group; it is not a scene ID.
- **Scene ID**: a stable source identifier for a physical scene, video, session or location.
- **Normal-road readiness gate**: a future pass/fail/unresolved source acceptance checklist;
  not part of the MVP.
- **Post-MVP extension**: overlays, review ledger, figures or readiness analysis. An extension
  does not block the core audit.

## User Scenarios & Testing

### User Story 1 — Reproduce the benchmark baseline (Priority: P1)

A reviewer runs one command against the local checkout and receives a schema-valid JSON summary
and a Markdown report derived from it. The report reproduces the accepted inventory,
instance/semantic invariant, coverage, category and object-scale values.

**Independent Test**: Run the CLI with a temporary output root. Assert the JSON validates against
the MVP schema, the report is re-rendered from the validated JSON bytes, and the report contains
the source JSON SHA-256. Confirm the accepted baseline values and that no figures, overlays or
readiness report are created.

**Acceptance Scenarios**:

1. **Given** the accepted checkout, **when** the audit runs into a temporary root, **then** it
   writes exactly `roadanomaly-eda.json` and `roadanomaly-eda.md`.
2. **Given** a documented claim and a computed value that differ, **when** the report is
   rendered, **then** both appear with their evidence class and definition.
3. **Given** a changed local file, **when** the audit computes the fingerprint, **then** it
   prints the historical and computed hashes/counts, exits `2`, and writes no output.

### User Story 2 — Inspect annotation integrity (Priority: P1)

A reviewer can see whether image/mask dimensions, semantic values, colour mapping, instance
ranges, the instance/semantic relationship, the order mapping and ROI bounds are consistent,
without altering `data/`.

**Independent Test**: Run the integrity tests on the accepted checkout. They assert 60/46/14/201,
46/46 exact instance/semantic equality, 35/46 order agreement, 11/201 out-of-bounds ROIs and
17/201 non-tight boxes. A temporary copy with an altered instance union fails with exit `2` and
prints the affected frame and extra/missing counts.

**Acceptance Scenarios**:

1. **Given** a corrupt frame or invalid mask, **when** the audit runs, **then** it names the
   path/invariant, exits `2` and writes no canonical output.
2. **Given** the accepted annotations, **when** the audit runs, **then** `data/` remains
   byte-for-byte unchanged.
3. **Given** an instance/semantic mismatch, **when** the audit detects it, **then** it prints
   every affected frame with extra/missing pixel counts, exits `2`, and writes no JSON or report.

### User Story 3 — Expose provenance, licensing and limitations (Priority: P2)

A reviewer can distinguish locally computed facts, documented local claims, upstream-unverified
claims and unresolved questions. The report lists credit gaps, source groups and the open
scientific items without making a legal conclusion.

**Independent Test**: Assert 60 credit entries, 24 missing licence tokens, four source groups
covering 13 frames, one four-frame group without a URL, the CC BY-SA 4.0 annotation claim, the MIT
code claim, `legal_conclusion: not_made`, and the open ADR-0010 threshold contradiction.

**Acceptance Scenarios**:

1. **Given** the credit file, **when** provenance is audited, **then** attribution, missing
   tokens, missing URLs and source groups are reported without a legal conclusion.
2. **Given** filename prefixes, **when** the report groups frames, **then** they are labelled
   object categories, never scenes or split units.
3. **Given** the ADR-0010 contradiction, **when** the report is rendered, **then** it remains
   `unresolved` and `open`.

## Edge Cases

- **Fingerprint drift**: report historical and computed hashes/counts, exit `2`, write no JSON
  or report; never replace the historical constant.
- **Missing/corrupt frame or label**: name the path, exit `2`, do not skip or synthesize.
- **Instance/semantic mismatch**: name each frame and extra/missing counts, exit `2`, no output.
- **Non-contiguous or duplicate instance IDs**: report the frame, exit `2`, do not renumber.
- **ROI outside the image or non-tight**: report the frame/instance, do not clip.
- **Mixed output pair after a crash**: JSON is authoritative; check mode detects a report/JSON
  mismatch. This is a documented limitation of per-file replacement, not a transaction claim.
- **No normal-road source**: irrelevant to the MVP; the readiness extension remains unresolved.
- **A future extension attempts to block the MVP**: the extension is out of scope and must be
  specified separately.

## Functional Requirements (MVP)

### Cross-cutting

- **FR-001**: The feature MUST remain in CRISP-DM phase 2 (data understanding). It MUST NOT
  decide a model, metric, threshold, class map, split, benchmark score or promotion.
- **FR-002**: The 60 benchmark frames are evaluation-only. Nothing may be fitted, selected,
  tuned or promoted on them.
- **FR-003**: The feature MUST NOT download, acquire, survey, rank or select a normal-road
  dataset; MUST NOT create a class map, manifest or split; and MUST NOT create split hashes or
  scene assignments.
- **FR-004**: `data/` and `data/credits.txt` MUST remain byte-for-byte read-only.
- **FR-005**: Computed findings MUST come from one implementation in `dl/data/audit.py`.
  Report values MUST come from the validated JSON summary, not from a second computation.
- **FR-006**: Every quantitative, provenance or licensing statement in the report MUST carry a
  visible evidence class: `computed_local`, `documented_local`, `upstream_unverified` or
  `unresolved`. A statement with no class is a defect.
- **FR-007**: The historical fingerprint, its fixed counts `677`/`13,135,474`, its recipe and
  its provenance caveat MUST be preserved. Drift MUST be reported as a hard failure and MUST NOT
  replace the baseline.
- **FR-008**: The audit outputs are validation evidence, not an experiment record or model
  performance claim.
- **FR-009**: The audit MUST run offline, without TensorFlow, a GPU or network access.
- **FR-010**: The feature MUST NOT modify the constitution, an accepted ADR, `docs/metrics.md`
  or `docs/dataset.md`. Contradictions are reported for later review.

### Benchmark audit

- **FR-011**: The audit MUST verify 60 frames, 60 label directories, the frame list, image
  dimensions/mode, missing/orphaned entries, semantic values `{0,2}`, the colour mapping,
  contiguous instance IDs and `cls=2`.
- **FR-012**: For every instance-annotated frame, the union of instance values `1..N` MUST equal
  the semantic pixels with value `2`. It MUST report 46 checked, 46 exact, 0 mismatched, the
  semantic-only exclusions (14), and extra/missing counts. A mismatch is a hard failure with
  exit `2`, no canonical output, and the affected frame/counts printed.
- **FR-013**: The audit MUST compute pooled coverage, per-frame minimum/maximum/median, the six
  frames below 1 % and the accepted six-decimal values. `coverage.definitions` MUST contain the
  named formulas for `pooled_fraction`, `per_frame_fraction`, `percent`, `median` and
  `below_one_percent`.
- **FR-014**: The audit MUST compute the five filename-prefix category counts and label them
  `object_category_not_scene`.
- **FR-015**: The audit MUST compare mask value `k` with the k-th instance entry and report
  35/46 agreement, 11/46 disagreement, the complete disagreement list and the weaker existing
  `max(mask) == len(instances)` check.
- **FR-016**: The audit MUST report 11/201 out-of-bounds ROIs, 17/201 non-tight instance boxes
  and 201/201 centroid containment, with half-open bounds and complete affected-item lists. It
  MUST NOT clip or rewrite annotations.
- **FR-017**: The audit MUST report object scale under named definitions: ROI area < 1024,
  both dimensions < 32, either dimension < 32, ROI equivalent square, ROI width/height and
  mask-pixel equivalent square. It MUST preserve 35/20/46 and the three medians.
- **FR-018**: The audit MUST run exact, decoded-pixel and stated dHash duplicate checks, report
  the method and its limits, and never claim more than the method establishes.
- **FR-019**: The audit MUST report 60 credit entries, 24 missing licence tokens, missing source
  URLs, four source groups covering 13 frames, and attribution. `source_url` is the last
  non-`creativecommons.org` URL in block/file order, or `null` if none.
- **FR-020**: The audit MUST report the annotation licence claim `CC BY-SA 4.0`, the code licence
  `MIT`, their sources/scope, and `legal_conclusion: not_made`. Missing per-image tokens remain
  `unresolved`, not “unlicensed.”
- **FR-021**: The audit MUST report the local citation, `release_identifier: null`,
  `upstream_status: upstream_unverified`, `scene_identity: unresolved`, false filename-prefix
  scene identity, and the ADR-0010 threshold contradiction in `provenance.unresolved_items`
  with `item_id`, `statement`, `evidence_class: unresolved`, source and `status: open`.
- **FR-022**: The report MUST summarize the accepted Stage 2 baseline, documented-claim
  comparisons, limitations and unresolved items, preserving the distinction between local and
  upstream evidence.
- **FR-023**: The Markdown report MUST contain the 10 sections defined in
  `contracts/eda-report.md`, include the source JSON SHA-256, contain no recomputed values and
  contain no registration, readiness or figure claim.
- **FR-024**: The JSON summary MUST validate against the single authoritative
  `contracts/audit-summary.schema.json` (Draft 2020-12). The report MUST be rendered from the
  validated JSON bytes; a report rendered from an unvalidated object is invalid.
- **FR-025**: Repeated runs on the same checkout and environment MUST produce byte-identical JSON
  and report. The only volatile field is `environment.commit`; check mode pins it to the committed
  value.
- **FR-026**: Tests MUST cover fingerprint, inventory, integrity, the instance/semantic
  invariant, coverage, categories, scale, mapping, ROI, duplicates, credits/provenance, schema,
  report-from-JSON, failure exits, output policy and check mode. They MUST run without
  TensorFlow, a GPU, network or a normal-road corpus.
- **FR-027**: A missing file, corrupt image, invalid mask, fingerprint drift, invariant failure
  or schema failure MUST fail with an actionable message; normal failures MUST not write a
  canonical JSON/report. The CLI MUST distinguish data/integrity failures (`2`), contract/output
  failures (`3`) and policy violations (`4`).

### Interface and reproducibility

- **FR-028**: The authoritative audit MUST live in `dl/data/audit.py` and be importable without
  TensorFlow.
- **FR-029**: `make data-audit` MUST generate the two outputs; `make data-audit-check` MUST
  validate them without writing.
- **FR-030**: The notebook `01_dataset_eda` remains a spec 002 presentation client; it MUST NOT
  duplicate authoritative statistics.
- **FR-031**: Audit tests MUST run under the fast profile with NumPy/Pillow and `jsonschema`.
- **FR-032**: The CLI MUST write only `roadanomaly-eda.json` and `roadanomaly-eda.md` under the
  configured output root, using temporary sibling files and per-file replacement. It MUST NOT
  write to `data/`, `docs/experiments/`, `configs/`, `specs/`, `docs/adr/` or any other output
  subdirectory.
- **FR-033**: `docs/README.md` and `docs/validation/requirements-matrix.md` MAY be updated only
  after evidence exists. A checked task or spec is not evidence.
- **FR-034**: The MVP MUST NOT depend on overlays, figures, a review ledger or a readiness gate.
  Those are extensions specified separately and cannot block core acceptance.

## Extension Requirements (Not MVP)

These are documented for a later approved change. They are not implemented, tested or required
for MVP acceptance.

- **EXT-01 — Visual overlays and review ledger**: generate deterministic semantic/instance
  overlays and a human-review CSV. See `contracts/visual-review-ledger.md`. This extension must
  not add fields to the MVP JSON schema.
- **EXT-02 — Aggregate figures**: render coverage, category, scale, ROI and credit figures from
  the validated JSON. Figures must be aggregate-only unless attribution is added.
- **EXT-03 — Normal-road readiness gate**: define and test the `NR-01`–`NR-13` gate with no
  source selected. See `contracts/normal-road-readiness.md`. It must not block the core audit or
  change P0 status.

## Key Entities

- **AuditResult**: complete immutable MVP JSON root containing environment, fingerprint,
  inventory, instance/semantic, coverage, categories, object scale, mapping, ROI, duplicates,
  credits, provenance, documented claims, limitations and claims.
- **Historical fingerprint**: accepted Stage 2 hash, recipe, counts and provenance caveat.
- **CoverageRecord** and **RoiRecord**: computed statistics with required `definitions` maps.
- **Claim**: evidence-classified report statement/value.
- **DocumentedClaim**: documented text compared with a local computed value.
- **Limitation**: an explicit method or evidence limit with an evidence class.
- **Source group**: attribution-derived group, not a scene.
- **Extension artifacts**: overlays, figures, ledger and readiness report; outside the MVP.

## Outputs

| Artifact | Path | Committed? | Content |
|---|---|---|---|
| EDA JSON | `docs/validation/roadanomaly-eda.json` | Yes | Complete schema-valid MVP summary |
| EDA report | `docs/validation/roadanomaly-eda.md` | Yes | Rendered from validated JSON |
| Audit implementation | `dl/data/audit.py` | Yes | Single authoritative implementation |
| Audit tests | `tests/dataset/test_dataset_audit.py` | Yes | Contract, invariant and failure tests |
| Command | `make data-audit` | Yes | Generate entry point |

The JSON does not contain the report hash. The report contains the JSON SHA-256. There are no
figures, overlays, ledger or readiness outputs in the MVP.

## Success Criteria

- **SC-001**: The fingerprint recipe and regression test reproduce the historical value and
  counts. A drift run exits `2`, prints historical/current values and counts, and writes no
  canonical output.
- **SC-002**: 100 % of report quantitative/provenance/licensing statements carry one of the four
  evidence classes; no claim is unlabelled.
- **SC-003**: The JSON validates against the MVP schema and the Markdown report is exactly the
  renderer output for those validated bytes; the report records the JSON SHA-256.
- **SC-004**: The report and JSON state 46/46 exact instance/semantic equality, 0 extra, 0
  missing and 14 semantic-only exclusions. A mismatch never appears as a valid zero-mismatch
  summary.
- **SC-005**: Coverage is reported as 9.849561 % pooled, 0.374674–42.328559 % per frame, median
  6.622938 %, with the six sub-1 % frames named and definitions present.
- **SC-006**: Object scale reports 35/201, 20/201, 46/201, 86.7 px, 85 × 107 px and 51.2 px with
  every named definition.
- **SC-007**: The report lists 35/46 mapping agreement, 11/46 disagreement, 11/201 out-of-bounds
  ROIs, 17/201 non-tight boxes and 201/201 centroids, with complete affected-item lists.
- **SC-008**: Repeated runs produce byte-identical JSON and report; check mode validates the
  committed pair and writes nothing.
- **SC-009**: `make lint type test` passes, and the audit tests run without TensorFlow, GPU,
  network or a normal-road corpus.
- **SC-010**: `data/`, `data/credits.txt`, `docs/metrics.md`, `docs/dataset.md`,
  `.specify/memory/constitution.md` and every file under `docs/adr/` are byte-for-byte unchanged.
- **SC-011**: Static inspection finds no authoritative EDA statistic implementation in
  notebooks.
- **SC-012**: The report states that P0-1 through P0-4 and G10 remain open and makes no model,
  metric, threshold or class-map decision.
- **SC-013**: The requirements matrix is not marked `implemented` on the strength of the spec or
  a checked task.

## Assumptions

- The accepted Stage 2 baseline is the regression target and the local checkout is the only
  benchmark source.
- The historical byte encoding is a local reconstruction. The audit reports that provenance
  caveat and does not claim the original Stage 2 implementation was recovered.
- NumPy, Pillow and `jsonschema` are declared in `requirements/dev.txt` and supplied by
  `make install`. The MVP does not require Matplotlib.
- A human reviewer may later add overlays, figures and readiness evidence through an extension,
  but the core audit is accepted without them.
- An all-unresolved readiness gate remains a valid future outcome; it is not part of MVP
  acceptance.

## Dependencies

- Constitution items 3, 4, 5, 8, 11, 12 and 13.
- ADR-0001 (evaluation-only benchmark), ADR-0007 (CRISP-DM phase 2) and ADR-0010 (model lineup
  and evaluation contract), with P0-1 through P0-4 open.
- `docs/dataset.md`, `data/readme.md`, `data/credits.txt`, `LICENSE` and `tests/dataset/`.
- Spec 002 and `dl/notebooks/README.md` for the notebook boundary.
- The accepted Stage 2 baseline, historical fingerprint and requirements matrix V1.3/G10.

## Out of Scope

- Acquiring, surveying, ranking or selecting a normal-road dataset.
- Creating a class map, manifest, split, split hash or scene assignment.
- Model training, selection, tuning, scoring, thresholding, inference or XAI.
- Visual overlays, review ledger, aggregate figures and readiness reporting; these are
  extensions.
- Modifying `docs/metrics.md`, `docs/dataset.md`, the constitution, an accepted ADR or `data/`.
- Updating the requirements matrix before evidence exists.
- Claiming legal redistribution rights or resolving P0-1 through P0-4.

## Review Checklist

- [ ] The MVP produces exactly a JSON summary and a report derived from validated JSON.
- [ ] The historical fingerprint and its fixed counts are preserved and drift is a hard failure.
- [ ] The 46/46 instance/semantic invariant and 14 semantic-only exclusions are explicit.
- [ ] Coverage, categories, object scale and ROI definitions are present in schema, model,
      report and tests.
- [ ] Fingerprint and integrity failures exit non-zero with actionable diagnostics and no
      canonical output.
- [ ] `data/`, protected docs and ADRs are unchanged.
- [ ] Overlays, figures, ledger and readiness are extensions, not blockers.
- [ ] Every MVP requirement maps to a task and a test.
- [ ] No class map, split, split hash, manifest or experiment record is created.
- [ ] P0-1 through P0-4 and G10 remain open.
