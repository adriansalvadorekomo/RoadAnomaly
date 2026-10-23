# Phase 0 Research: RoadAnomaly dataset audit MVP

**Feature**: `003-dataset-understanding` · **Date**: 2026-10-22

This file resolves the implementation choices behind [plan.md](./plan.md). It introduces no new
requirements or evidence. The values below are regression definitions for the accepted Stage 2
baseline.

## Scope and sources

The audit reads only:

- `data/frame_list.json`, `data/frames/*.webp`, `data/frames/*.labels/`, `data/credits.txt` and
  `data/readme.md`;
- the accepted baseline and definitions in [spec.md](./spec.md);
- the existing dataset tests in `tests/dataset/`;
- ADR-0001, ADR-0007 and ADR-0010 for evaluation-only and open-item boundaries.

It does not read or download a normal-road corpus, a candidate dataset or network content.

## R1 — One authoritative audit module

**Decision**: Put all computation, CLI parsing, JSON serialization and report rendering in
`dl/data/audit.py`; add `dl/data/__init__.py` as a package marker. Notebooks, tests and Make
targets import this module. The CLI is `python -m dl.data.audit`.

**Rationale**: The spec requires one shared implementation and forbids notebook-local statistics.
A single small module keeps the schema, definitions and renderer from drifting.

**Alternatives considered**: A notebook implementation (rejected by spec 002 and FR-005); one
module per statistic (unnecessary for this surface); a separate report package (unnecessary
abstraction).

## R2 — JSON is authoritative; report is derived

**Decision**: Build one complete immutable `AuditResult` with 16 root fields. Serialize it
deterministically, validate it with Draft 2020-12, and render the Markdown report only from the
validated JSON bytes plus their SHA-256. The JSON has no report hash, no output manifest and no
self-hash. The report records the source JSON digest. A canonical result must be complete: every
root field is populated before validation; partial or placeholder output is invalid.

**Rationale**: The report cannot disagree with the JSON if it is a pure renderer. A one-way
digest avoids a circular dependency without a staging transaction.

**Alternatives considered**: Render Markdown directly from images (rejected: two computations);
hand-maintained report tables (rejected by FR-005); JSON generated from the report (rejected: the
report is not a stable input); report hash inside JSON plus JSON hash inside report (rejected:
circular); output manifest (unnecessary for two files).

## R3 — Historical fingerprint

**Decision**: Reproduce the historical value exactly:

1. Enumerate regular files under `data/`, recursively, without following symlinks.
2. Sort by path relative to `data/`, POSIX separators, byte order.
3. Initialize SHA-256.
4. For each file, update with the UTF-8 relative path, one NUL byte, and the raw 32-byte SHA-256
   digest of the file content.
5. Append no trailing NUL or newline.
6. Hex-encode the final digest.

The expected value is
`7c16ab39607d68a66bc2f4ac321933f64221d62980119ea780af5abf2a99f4e2` over `677` files and
`13,135,474` bytes. The record keeps the historical hash and counts as constants and computes the
current checkout counts separately. A mismatch prints the historical and computed hashes plus
both count pairs, exits `2`, and writes no canonical output. The historical constants are never
replaced.

**Provenance caveat**: The recipe is a reconstruction from the documented construction. No
Stage 2 script is present in the repository. The report distinguishes the locally verified match
from the unverified provenance of the original byte layout and does not claim
`original_implementation_verified`.

**Alternatives considered**: Replacing the historical value with a new scheme (forbidden); hashing
only frame images (does not cover the 677-file baseline); adding a trailing separator (does not
reproduce the value).

## R4 — Frame, label and mask semantics

**Decision**:

- Frame order is `data/frame_list.json` order. Check it against the 60 `*.webp` files and reject
  missing or orphaned entries.
- Every frame has a `.labels/` directory, `labels_semantic.png` and `labels_semantic_color.png`.
- A frame is instance-annotated when `index.json` exists; it must also have
  `labels_instance.png`. A frame without `index.json` is semantic-only. Expected: 46 instance and
  14 semantic-only.
- Semantic masks are 2-D uint8 arrays at 1280×720 with values in `{0,2}` and at least one anomaly
  pixel.
- The colour visualization is RGB at the same size. Normal `(0,0,0)`, anomaly `(255,69,0)`; no
  other colour.
- Instance masks are 2-D integer arrays with values `1..N`; zero is background. `N` equals the
  number of `index.json` entries. Every instance has `cls = 2`.
- **Order mapping**: compare pixel value `k` with `instances[k-1].id`. A frame agrees only when
  every `k` matches. Baseline: 35/46 agree, 11/46 disagree. The existing
  `max(mask) == len(instances)` test is recorded as the weaker check, not promoted.
- **Instance/semantic consistency**: for every instance frame, compare
  `union(mask pixels 1..N)` with semantic pixels equal to `2`. Baseline: 46/46 exact, 0 extra,
  0 missing, 14 semantic-only excluded. A mismatch is a hard failure: print each affected frame
  with extra/missing counts, exit `2`, write no output, never edit a mask.
- The schema's success-only `instance_semantic` shape applies after the invariant passes; it does
  not force a mismatch to be serialized as zero.

**Rationale**: These definitions reproduce the accepted baseline and keep the ambiguous
instance-ID relationship visible instead of renumbering or normalizing it.

**Alternatives considered**: Mapping by `id` lookup rather than array position (hides the
discrepancy); renumbering masks (forbidden); treating semantic-only frames as invalid (they are
part of the accepted baseline).

## R5 — Coverage, categories and object scale

**Decision**:

- **Coverage**: anomaly pixels are semantic value `2`. Per-frame coverage is
  `anomaly_pixels / (1280×720)`. Pooled coverage is `sum(anomaly_pixels) / sum(pixels)` over
  60 frames. Median is the median of the 60 per-frame fractions. Six frames are below 1 %.
  Six-decimal values: `9.849561 %` pooled, `0.374674–42.328559 %` range, `6.622938 %` median.
  `coverage.definitions` carries `pooled_fraction`, `per_frame_fraction`, `percent`, `median` and
  `below_one_percent`; the renderer only quotes the map.
- **Categories**: frame-name prefix before the first digit (`animals`, `obstacles`, `cones`,
  `lost_tires`, `vehicle`). Counts `31/15/8/3/3`. Label them **object categories**, never scene
  IDs or split units.
- **ROI area**: `(x1 - x0) × (y1 - y0)` on half-open extents. `area < 1024 px²` gives 35/201.
- **Both-dimension threshold**: `width < 32 and height < 32` gives 20/201. **Either-dimension
  threshold** gives 46/201.
- **ROI equivalent square**: `sqrt(ROI area)`; median 86.7 px.
- **ROI bounding box**: median width 85 px, median height 107 px.
- **Mask-pixel equivalent square**: `sqrt(count of nonzero instance-mask pixels)`; median 51.2 px.
- `object_scale.definitions` carries all six formulas. The report does not present a single
  “87 × 87” figure as the only truth.

**Rationale**: The documented claim and local definitions disagree. Reporting each named
definition preserves both without silently choosing one.

**Alternatives considered**: Use only the documented 87 × 87 figure (unsupported); use a single
small-object definition (hides 20/35/46); compute scale from bounding boxes only (not the ROI
contract).

## R6 — ROI bounds and centroid containment

**Decision**: Treat `roi_rect` as `[[x0,y0],[x1,y1]]` with half-open right/bottom extents.

- **Out of bounds** when `x0 < 0 or y0 < 0 or x1 > 1280 or y1 > 720`. Baseline 11/201. A ROI
  ending exactly at 1280 or 720 is inside.
- **Non-tight instance box** when the inclusive mask pixel box for value `k` is not strictly
  inside the half-open ROI: `bx0 < x0 or by0 < y0 or bx1 >= x1 or by1 >= y1`. Baseline 17/201.
  A box touching the ROI edge is non-tight under this convention.
- **Centroid**: `((bx0 + bx1) / 2, (by0 + by1) / 2)`. Containment when `0 <= cx < 1280` and
  `0 <= cy < 720`; baseline 201/201 inside.
- `roi.definitions` carries `out_of_bounds`, `non_tight` and `centroid_containment`.
- `crop_rect` is provenance only, not the ROI bound used for these findings.

The audit never clips or rewrites a ROI.

**Rationale**: The half-open convention and order mapping reproduce the accepted 11/201 and
17/201 findings. The report makes the convention explicit.

**Alternatives considered**: Inclusive right/bottom bounds (produces 13 and 15, disagreeing with
the baseline); clipping ROIs (forbidden); treating a boundary touch as tight (disagrees with
17/201).

## R7 — Duplicate checks

**Decision**: Run three checks and report their limits:

- exact raw-file SHA-256 duplicates;
- decoded RGB pixel-buffer SHA-256 duplicates;
- difference hash on a 9×8 grayscale resize (64 bits), reporting pairs at Hamming distance ≤6.

The baseline has no exact, decoded or dHash-close pairs. The report says this is method-limited
and not proof that no near-duplicates exist.

**Rationale**: The spec requires exact/decoded checks and a stated dHash check without claiming
more than the method establishes.

**Alternatives considered**: Perceptual embeddings (require a model); claiming “no duplicates”
without a method (overclaim); omitting the dHash limit (misleading).

## R8 — Credits, licences and source groups

**Decision**:

- Parse `credits.txt` into blocks. A block starts with one or more non-indented frame stems,
  followed by indented author/source lines. Ignore the preamble. Every one of the 60 frames
  appears in exactly one block.
- **Explicit licence token**: case-insensitive `CC0`, `CC BY`/`CC BY-SA` with optional version,
  or `public domain`. Baseline 24 frames without a token; mark them `unresolved`, not
  “unlicensed.”
- **Source URL**: the last URL in the block, in file order, that is not a
  `creativecommons.org` licence URL. If none, `null`. This selects the image/source page when a
  block also contains author-profile or licence URLs. Baseline: one four-frame group without a
  URL.
- **Source group**: frames sharing the same source URL. If a block has no source URL, frames
  sharing that block form the group. Baseline: four multi-frame groups covering 13 frames:
  lost_tires03/08/09 (3), cones07/cones08_can (2), obstacles03–06 (4), obstacles12_rocks2/4/5/6
  (4, no URL).
- Report credit coverage, missing tokens, missing URLs, groups and that local attribution is not
  proof of redistribution rights. Do not make a legal conclusion.
- Report global licence claims separately: annotations **CC BY-SA 4.0** from `data/credits.txt`
  and `docs/dataset.md`; code **MIT** from `LICENSE`, scope `source code; data and annotations
  excluded`. Both are `documented_local`, not independently verified. `legal_conclusion` is
  always `not_made`.

**Rationale**: These definitions reproduce 60 entries, 24 missing tokens, one four-frame group
without a URL and 13 frames in four source groups, while preserving the distinction between
attribution, source identity and scene identity.

**Alternatives considered**: Grouping by Creative Commons URL (groups by licence, not source);
treating a missing token as no licence (overclaim); using credit groups as scene IDs (forbidden).

## R9 — Extensions are not MVP

**Decision**: The MVP has no overlays, figures, review ledger or readiness report.

- **EXT-01 overlays/ledger** is documented in `contracts/visual-review-ledger.md`; it requires a
  separate approved schema/report/test change.
- **EXT-02 figures** are aggregate-only and rendered from validated JSON; they are not in the
  MVP because they add a dependency and determinism surface without being necessary for the core
  evidence.
- **EXT-03 readiness** is documented in `contracts/normal-road-readiness.md`; no source is
  selected, and an all-unresolved gate is a future outcome.

**Rationale**: The user’s priority is a small audit that can be produced and tested end to end.
Extensions must not block core acceptance or make check mode depend on Git-ignored artifacts.

**Alternatives considered**: Include all extensions in the first delivery (rejected: scope and
coupling); delete extension contracts (rejected: they document known future work); silently omit
extensions (rejected: the spec must be explicit).

## R10 — CLI, output policy and check mode

**Decision**:

- `make data-audit` runs `python -m dl.data.audit` with defaults `data` and `docs/validation`.
- `make data-audit-check` runs `--check`, writes nothing, and validates the committed pair.
- Output root must exist. Inside the repository only `docs/validation` is allowed; temporary
  outside roots are allowed for tests. Only `roadanomaly-eda.json`/`.md` and their `.tmp` siblings
  may be written. No subdirectories, artifact root, staging directory or journal.
- Generate sequence: compute; serialize; validate; render report from validated JSON; write
  temporary siblings; `os.replace` JSON then report; clean temporaries.
- A normal failure before replacement leaves the previous pair unchanged. A crash or a failure of
  the second replacement can leave a mixed pair; JSON remains authoritative and check mode detects
  the report mismatch. This limitation is documented, not hidden.
- Exit codes: `0` success/consistent; `1` committed output mismatch; `2` data/fingerprint/integrity
  failure; `3` input/schema/render/I/O failure; `4` output-policy violation.
- `environment.commit` is the only volatile field. Check mode pins it to the committed value; no
  git ancestry lookup is required.
- `environment.command` is always `make data-audit`, never the check invocation.

**Rationale**: A documented command and non-writing check satisfy FR-029 and SC-008 without a
transaction engine. Per-file atomic writes are sufficient when the JSON is authoritative and
check mode can detect a mixed pair.

**Alternatives considered**: Single in-place write (can truncate evidence); journal/backup
transaction (overkill for two files and hard to test); relying on `git diff` (does not cover a
committed pair or a clean checkout); check mode requiring Git-ignored artifacts (not
self-contained).

## R11 — Test strategy

**Decision**: Add `tests/dataset/test_dataset_audit.py`, marked `dataset`, covering:

- historical fingerprint value, historical 677/13,135,474 counts, current counts, deterministic
  recomputation and drift exit `2` with no output;
- 60 frames, 60 label directories, 46 instance/14 semantic-only, image dimensions/mode, semantic
  values and colour mapping;
- contiguous instance IDs, `cls=2`, order mapping 35/46 and 11/46 with complete lists;
- instance/semantic 46/46, 0/0, 14 excluded; a temporary altered mask exits `2`, prints the
  affected frame and extra/missing counts, writes no output and leaves masks unchanged;
- coverage, categories, scale and every definitions map;
- ROI 11/201, 17/201, 201/201 with complete affected lists and no clipping;
- duplicate methods and limits;
- 60 credit entries, 24 missing tokens, four source groups/13 frames, one group without URL,
  last-non-CC URL selection, annotation/code licence claims and `legal_conclusion: not_made`;
- provenance flags, ADR-0010 open item, P0/G10 open, documented-claim treatments and limitations;
- schema meta-validation, 16 root fields, generated-summary validation, extension-field rejection;
- report headings, JSON parity, source digest, JSON-has-no-report-hash, deterministic bytes;
- generate exactly two files, check mode match/mismatch, mixed-pair detection, no writes;
- output policy, temp cleanup, normal failure preserves old pair, traversal/symlink rejection;
- `data/` and protected docs/ADRs unchanged; no notebook statistics; no split/class map/manifest.

Tests use `tmp_path` and do not write to `docs/validation/` or `data/`. No test is skipped. Tests
do not import TensorFlow, Matplotlib or perform network access.

**Rationale**: FR-026 and SC-009 require meaningful tests for every MVP requirement, including
failure paths and the read-only boundary. The historical value is a regression target, not a
value to repair.

**Alternatives considered**: Repository-wide “no manifest exists” assertions (run-scoped checks
are more precise); tests that need a normal-road corpus (impossible and unnecessary); snapshotting
every output byte from a hand-written fixture (brittle).

## R12 — No source, no P0 closure, no new ADR

**Decision**: The plan creates no ADR, source ranking, class map, split, manifest or experiment
record. The JSON and report record P0-1 through P0-4 and G10 as open and carry the ADR-0010
threshold contradiction as an `unresolved`/`open` item. No unresolved scientific item is silently
closed.

**Rationale**: This is a phase 2 evidence feature. A new ADR is reserved for a contract or
invariant change, which this feature does not make.

**Alternatives considered**: A new ADR for the audit format (CLI/schema contracts are sufficient
and reversible); closing P0 items from the audit (out of scope and unsupported).

## R13 — Schema and report contract

**Decision**: `contracts/audit-summary.schema.json` is the single authoritative Draft 2020-12
schema with 16 root fields and no extension fields. `contracts/eda-report.md` defines ten
sections. Every numeric/table report value comes from the validated JSON or a `Claim`; the only
additional report value is the source JSON SHA-256. Meta-validate the schema with
`Draft202012Validator.check_schema` and validate a generated summary with
`Draft202012Validator(schema).validate`. `jsonschema` is a mandatory runtime dependency. Do not
claim schema validation before the commands have actually run.

**Rationale**: The report is an output, not a second computation. A single schema catches summary
drift; meta-validation catches contract syntax errors.

**Alternatives considered**: Hand-maintained report headings (not testable); treating schema
syntax as sufficient (does not validate the emitted summary); a custom validator (unnecessary).

## Resolved open questions

There are no remaining `NEEDS CLARIFICATION` items. The following are intentionally unresolved
**scientific** items, not planning gaps:

- P0-1: class names, IDs and ignore list;
- P0-2: metric placement;
- P0-3: benchmark scoring;
- P0-4: threshold protocol, including the ADR-0010 contradiction;
- G10: no pinned normal-road release, scene list or manifest.

The MVP reports these as open. It does not resolve them.
