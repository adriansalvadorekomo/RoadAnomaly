# Tasks: RoadAnomaly dataset audit MVP

**Input**: Design documents from `/specs/003-dataset-understanding/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Every implementation task includes its contract test in
`tests/dataset/test_dataset_audit.py`. Write the assertion before or with the implementation and
confirm the expected failure. No test may be skipped. Tests must run without TensorFlow, a GPU,
network, Matplotlib, a normal-road corpus or a generated canonical pair.

**Scope guard**: read-only over `data/`; no model fitting, selection, tuning, scoring or
promotion; no source acquisition, survey or ranking; no class map, split, split hash, manifest or
experiment record. Visual overlays, figures, the review ledger and normal-road readiness are
extensions, not tasks in this MVP.

## Format

- `[P]` means a setup task with different files and no dependency on another setup task.
- Every task names the exact file or output it touches.
- Canonical output is written only in T026. Every earlier checkpoint uses a temporary root.

## Phase 1: Setup

- [x] T001 [P] Confirm `requirements/dev.txt` declares `jsonschema>=4.20`, NumPy and Pillow for the
  audit; leave the pre-existing Matplotlib dependency declaration intact; do not add a Matplotlib
  import or make Matplotlib an MVP dependency; confirm `make install` supplies the declared
  packages.
- [x] T002 [P] Create `dl/data/__init__.py` with a module docstring and
  `from __future__ import annotations`; no computation or CLI logic.
- [x] T003 [P] Add `data-audit` and `data-audit-check` to `Makefile`, both invoking
  `PYTHONDONTWRITEBYTECODE=1 $(BIN)/python -m dl.data.audit` (the second with `--check`); add
  both to `.PHONY`; no network or TensorFlow dependency.
- [x] T004 [P] Create `tests/dataset/test_dataset_audit.py` with `pytestmark = pytest.mark.dataset`,
  standard-library/test imports, and `tmp_path` fixtures for data/output roots; add no
  implementation duplication.

## Phase 2: Foundation

- [x] T005 Define the 16-field `AuditResult` and its typed records in `dl/data/audit.py`:
  `environment`, `fingerprint`, `inventory`, `instance_semantic`, `coverage`, `categories`,
  `object_scale`, `instance_mapping`, `roi`, `duplicates`, `credits`, `provenance`,
  `documented_claims`, `limitations` and `claims`. Encode the fixed schema version, historical
  hash `7c16…f4e2`, counts `677`/`13,135,474`, fingerprint recipe and `local_reconstruction`
  caveat. Do **not** define `ReportContext`, `PublicationPlan`, `OutputManifest`, overlay,
  ledger or readiness types.
- [x] T006 Define `AuditDataError`, `AuditContractError` and `AuditOutputPolicyError`, the exit
  codes `0`–`4`, and the two-file `OutputPaths` policy: destination names
  `roadanomaly-eda.json`/`.md`, temporary siblings, existing output root, only `docs/validation`
  inside the repository, outside-repository temporary roots, and traversal/symlink rejection.
- [x] T007 Implement deterministic JSON serialization and validation in `dl/data/audit.py`:
  UTF-8, sorted keys, LF, one trailing newline, no timestamp; validate with
  `jsonschema.Draft202012Validator` against
  `specs/003-dataset-understanding/contracts/audit-summary.schema.json`; reject an incomplete
  result, `None` mandatory value or placeholder with `AuditContractError`; never repair or patch
  a summary.
- [x] T008 Implement the CLI in `dl/data/audit.py`:
  `python -m dl.data.audit [--check] [--data-root PATH] [--output-root PATH]`; defaults `data`
  and `docs/validation`; `--check` writes nothing; generate dispatches to computation, JSON
  validation, report rendering and the two replacements; every non-zero exit prints an actionable
  path or invariant.
- [x] T009 Add schema and output-policy tests: `Draft202012Validator.check_schema` passes; the
  schema has exactly 16 required root fields; `additionalProperties` is false at the root;
  extension fields (`outputs`, `visual_review`, `readiness`, `overlays`, `figures`) are rejected;
  wrong in-repository output roots, missing output roots, subdirectories and symlink escapes are
  rejected with the documented exit code.

## Phase 3: Benchmark computation

- [x] T010 Implement fingerprint and inventory in `dl/data/audit.py`: enumerate regular files
  under the configured data root without following symlinks; sort POSIX-relative paths; hash
  `UTF-8 path + NUL + raw 32-byte SHA-256` with no trailing separator; require the historical
  value and counts; compute current file/byte counts; read `frame_list.json`; require 60 frames,
  60 label directories, 46 instance and 14 semantic-only; build canonical `frames/<name>` paths.
  Test the historical value, counts, frame counts, complete inventory and a temporary-copy drift
  that exits `2` with historical/current diagnostics and no output.
- [x] T011 Implement frame, semantic and instance loading in `dl/data/audit.py`: decode RGB
  1280×720 WebP; require semantic and colour masks; accept only semantic values `{0,2}` and
  colours `(0,0,0)`/`(255,69,0)`; require `labels_instance.png` and `index.json` for instance
  frames; validate contiguous `1..N`, non-empty masks and `cls=2`; catch decoder failures and
  report the exact path. Test missing, corrupt and invalid inputs with no skip, repair, renumber
  or clipping; assert `inventory.annotation_integrity` records semantic values `[0,2]`, colour
  mapping, class ID, contiguous IDs, complete label files and decodable frames.
- [x] T012 Implement the instance/semantic invariant in `dl/data/audit.py`: for each of the 46
  instance frames, compare `union(mask values 1..N)` with semantic value `2`; require 46/46 exact,
  0 extra, 0 missing and 14 semantic-only exclusions; on mismatch print every affected frame with
  extra/missing counts, exit `2`, and write no JSON or report. Test the success shape and a
  temporary altered mask that fails actionably.
- [x] T013 Implement coverage in `dl/data/audit.py`: count semantic value `2` per frame; compute
  total anomaly pixels, `55,296,000` total pixels, six-decimal pooled fraction/percent,
  per-frame fraction/percent, minimum `0.374674`, maximum `42.328559`, median `6.622938`, the six
  sorted sub-1 % frames and all five `definitions` keys. Test every value and definition.
- [x] T014 Implement categories and object scale in `dl/data/audit.py`: derive prefix before the
  first digit; require counts `31/15/8/3/3` and classification `object_category_not_scene`;
  compute `35/20/46`, medians `86.7/85.0/107.0/51.2`, denominator `201` and all six definition
  keys. Test values, definitions and that prefixes are not scenes.
- [x] T015 Implement instance mapping and ROI in `dl/data/audit.py`: compare mask value `k` with
  `instances[k-1].id`; require 35/46 agreement, 11/46 disagreement, complete sorted
  `disagreeing_frames` and `mismatches`; record the weaker `max(mask) == len(instances)` check;
  compute 11/201 out-of-bounds, 17/201 non-tight and 201/201 centroids with complete affected
  lists and all three ROI definitions. Test counts, list lengths and every affected item; assert
  no clipping or mask rewrite.
- [x] T016 Implement duplicate checks in `dl/data/audit.py`: exact raw-file SHA-256 pairs, decoded
  RGB pixel-buffer pairs, and 9×8 grayscale dHash pairs at Hamming distance ≤6; store
  `dhash_method` and method limitations. Test empty baseline lists, method text and that the
  limitation is not a “no duplicates” proof.
- [x] T017 Implement credits and licensing in `dl/data/audit.py`: parse `data/credits.txt` blocks
  (frame stems plus indented lines); require 60 unique entries; detect licence tokens and select
  `source_url` as the last non-`creativecommons.org` URL or `null`; report 24 missing tokens, the
  four obstacles12 missing URLs, four source groups covering 13 frames; record `CC BY-SA 4.0`,
  `MIT`, sources, scope and `legal_conclusion: not_made`. Test URL selection, missing tokens,
  groups and licence claims.
- [x] T018 Implement provenance, documented claims and limitations in `dl/data/audit.py`: record
  Lis et al. ICCV 2019, `release_identifier: null`, `upstream_unverified`,
  `scene_identity: unresolved`, false scene/redistribution claims, `normal_road_source_selected:
  false`, P0-1–P0-4 and G10 `open`, and the ADR-0010 unresolved item with `statement`, source and
  `status: open`; create the six documented-claim comparisons and baseline limitations. Test
  every flag, treatment and open item.
- [x] T019 Assemble claims and the complete result in `dl/data/audit.py`: every report
  numeric/table statement gets a stable `claim_id`, evidence class, value, definition and source;
  no evidence class is omitted; no placeholder remains. Test claim coverage, completeness of all
  16 root fields and that a missing or incomplete component is rejected before output.

## Phase 4: Report, generation and check

- [x] T020 Implement `render_report(validated_summary, source_json_sha256)` in `dl/data/audit.py`:
  emit the ten sections from `contracts/eda-report.md` in order, using only the validated summary
  plus the source digest; do not load images or recompute a value; include the JSON SHA-256, the
  claim table, complete affected-item lists, ADR-0010 and P0/G10 statements, and the extension
  disclaimer. Test headings, parity, digest and absence of figures/readiness claims.
- [x] T021 Implement end-to-end generate mode in `dl/data/audit.py`: compute, serialize, validate,
  render, write the two temporary siblings, `os.replace` JSON then report, remove temporaries and
  return `0`. Test a temporary-root run produces exactly the two files; the JSON schema validates;
  the report equals a fresh render from committed JSON; the JSON has no report hash; repeated runs
  are byte-identical; no canonical path is touched.
- [x] T022 Add generation failure tests: fingerprint drift, missing file, corrupt WebP, invalid
  mask and instance/semantic mismatch each exit `2` with the expected diagnostic and no output;
  schema/render/write failures before either replacement exit `3`; temporary files are removed; a
  failure before either replacement leaves a pre-existing output pair byte-identical. A simulated
  second-replacement failure is covered by the mixed-pair test in T023/T024.
- [x] T023 Implement check mode in `dl/data/audit.py`: validate the committed JSON, pin
  `environment.commit`, recompute the result and compare all other fields, re-render the report
  from validated committed JSON and compare bytes and source digest; write nothing. Test exit `0`
  on a consistent pair, `1` on a report/JSON mismatch (including a simulated mixed pair), `2` on
  data drift, `3` on schema/read failure, and assert no filesystem changes.
- [x] T024 Add output-policy tests: only two filenames are accepted; an in-repository root other
  than `docs/validation` exits `4`; a missing output root exits `3`; a temporary outside root is
  allowed; no subdirectory/overlay/figure/ledger/readiness file is created; traversal and symlink
  escape exit `4`; normal failure leaves old files and removes temporaries.

## Phase 5: Acceptance

- [x] T025 Run a complete audit into `/tmp/opencode/audit-mvp` and inspect the JSON/report:
  fingerprint 677/13,135,474 match; 60/60/46/14; 46/46, 0/0, 14; coverage `9.849561`,
  `0.374674–42.328559`, `6.622938`, six sub-1 % frames; categories `31/15/8/3/3`; scale
  `35/20/46` and the scale medians; mapping `35/46` with 11 items; ROI `11/201`, `17/201`,
  `201/201` with complete lists; duplicates method-limited; 60 credits, 24 missing tokens, four
  groups/13 frames; ADR-0010 open. Confirm no `docs/validation` output and `data/` unchanged.
- [x] T026 After T025 passes, run `make data-audit` once and `make data-audit-check`; confirm the
  canonical pair is written, check exits `0`, and the report's source digest matches the JSON.
  Do not hand-edit either file. This is the first canonical evidence for the feature.
- [x] T027 Run the final quality and scope gate: `make lint type test`, `make test-fast`,
  `make data-check`, schema meta-validation, `git status --short`, `git diff -- data`,
  `git diff -- docs/experiments`, `git diff -- docs/metrics.md docs/dataset.md
  .specify/memory/constitution.md docs/adr`, and the static notebook scan. Confirm no
  data/protected/ADR change, no split/class map/manifest, no notebook statistics, no canonical
  output from a component checkpoint, and no requirements-matrix `implemented` claim without
  evidence. Leave visual review, figures and readiness unimplemented.

## Dependencies and execution order

- T001–T004 are independent setup tasks and may run in parallel.
- T005–T009 block all computation. They edit the same module/test file, so run serially.
- T010–T019 are serialized because they share `dl/data/audit.py` and the test file.
- T020–T024 depend on the complete result and validated JSON from T007/T019.
- T025 depends on T020–T024. T026 depends on T025. T027 depends on T026.

Stop instead of weakening an assertion if a baseline value, invariant, schema check or output
policy fails. A missing prerequisite is a finding, not permission to invent data, a split, a class
map, a manifest or a placeholder report.

## Extensions (not tasks, not blockers)

- **EXT-01**: visual overlays and review ledger; `contracts/visual-review-ledger.md`.
- **EXT-02**: aggregate figures from validated JSON.
- **EXT-03**: `NR-01`–`NR-13` normal-road readiness; `contracts/normal-road-readiness.md`.

These require a separate approved change. They do not add fields to the MVP schema or tests and
must not block T026/T027.

## Requirement traceability

| Requirement | Implementation and verification |
|---|---|
| FR-001 | T019, T025, T027 |
| FR-002 | T019, T025, T027 |
| FR-003 | T008, T025, T027 |
| FR-004 | T011, T022, T025, T027 |
| FR-005 | T002, T005, T019, T020, T025 |
| FR-006 | T018, T019, T020 |
| FR-007 | T010, T021, T022, T025 |
| FR-008 | T020, T027 |
| FR-009 | T008, T027 |
| FR-010 | T024, T025, T027 |
| FR-011 | T010, T011, T021 |
| FR-012 | T012, T021, T022 |
| FR-013 | T013, T021 |
| FR-014 | T014, T021 |
| FR-015 | T015, T021 |
| FR-016 | T015, T021 |
| FR-017 | T014, T021 |
| FR-018 | T016, T021 |
| FR-019 | T017, T021 |
| FR-020 | T017, T021 |
| FR-021 | T018, T021 |
| FR-022 | T018, T020, T021 |
| FR-023 | T020, T021 |
| FR-024 | T007, T009, T020, T021 |
| FR-025 | T007, T021, T023, T026 |
| FR-026 | T009, T020, T021, T022, T023, T024, T025 |
| FR-027 | T008, T012, T022, T024 |
| FR-028 | T002, T005, T008 |
| FR-029 | T003, T008, T026 |
| FR-030 | T025, T027 |
| FR-031 | T001, T004, T025 |
| FR-032 | T006, T008, T024 |
| FR-033 | T027 |
| FR-034 | T027 |
| SC-001 | T010, T021, T022, T026 |
| SC-002 | T018, T019, T020 |
| SC-003 | T007, T009, T020, T021, T023 |
| SC-004 | T012, T021, T022 |
| SC-005 | T013, T021 |
| SC-006 | T014, T021 |
| SC-007 | T015, T021 |
| SC-008 | T007, T021, T023, T026 |
| SC-009 | T025, T027 |
| SC-010 | T024, T025, T027 |
| SC-011 | T027 |
| SC-012 | T018, T020, T027 |
| SC-013 | T027 |
