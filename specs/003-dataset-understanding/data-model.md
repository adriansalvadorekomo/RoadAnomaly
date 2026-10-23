# Phase 1 Data Model: RoadAnomaly dataset audit MVP

**Feature**: `003-dataset-understanding` · **Date**: 2026-10-22

This model defines the 16 root fields of the canonical JSON summary and the derived Markdown
report. It adds no dataset manifest, class map, split, overlay, ledger or readiness entity. Field
names are normative for `contracts/audit-summary.schema.json`.

## 1. Aggregate root

### `AuditResult`

| Field | Type | Required | Rule |
|---|---|---|---|
| `schema_version` | string | yes | Exactly `"1.0"` |
| `environment` | `EnvironmentRecord` | yes | Commit, Python/dependency versions, canonical command |
| `fingerprint` | `FingerprintRecord` | yes | Historical and matched current fingerprint |
| `inventory` | `InventoryRecord` | yes | 60 frames, 60 label directories |
| `instance_semantic` | `InstanceSemanticRecord` | yes | Success-only 46/46 exact relationship |
| `coverage` | `CoverageRecord` | yes | Pooled, per-frame, median, sub-1 % frames and definitions |
| `categories` | `CategoryRecord` | yes | Five object-category counts |
| `object_scale` | `ScaleRecord` | yes | Named definitions and medians |
| `instance_mapping` | `MappingRecord` | yes | 35/46 agreement, 11/46 disagreement |
| `roi` | `RoiRecord` | yes | Bounds, non-tight findings and definitions |
| `duplicates` | `DuplicateRecord` | yes | Exact, decoded and dHash results |
| `credits` | `CreditRecord` | yes | Coverage, missing tokens, source groups |
| `provenance` | `ProvenanceRecord` | yes | Citation, upstream uncertainty and open items |
| `documented_claims` | list[`DocumentedClaim`] | yes | Side-by-side claim comparisons |
| `limitations` | list[`Limitation`] | yes | Method and evidence limits |
| `claims` | list[`Claim`] | yes | Evidence-classified report claims |

Invariants:

1. No field represents a split, split hash, class map, manifest, source ranking, overlay, ledger,
   figure or readiness status.
2. Every numeric/table value in the report has a corresponding typed field or `Claim`.
3. Serialization is UTF-8, sorted keys, LF and one trailing newline. No timestamp is emitted.
4. `environment.commit` is the only volatile field. Check mode pins it to the committed value.
5. A complete result is serializable only when every root field is populated and non-placeholder.
6. Fingerprint drift is a hard failure before `AuditResult` assembly. It is not serialized.
7. An instance/semantic mismatch is a hard failure before `AuditResult` assembly. It is never
   coerced into the success-only `InstanceSemanticRecord`.
8. The JSON is authoritative. The report is rendered from the validated JSON bytes and records
   their SHA-256; the JSON contains no report hash.

## 2. Environment and fingerprint

### `EnvironmentRecord`

| Field | Type | Rule |
|---|---|---|
| `commit` | string | Full 40-hex source commit recorded at generation |
| `python` | string | `platform.python_version()` |
| `numpy` | string | Installed version |
| `pillow` | string | Installed version |
| `jsonschema` | string | Installed version used for mandatory validation |
| `command` | string | Fixed canonical `make data-audit`; never `sys.argv` or the check invocation |
| `audit_version` | string | Module contract version, exactly `1.0` |

No hostname, username, absolute workspace path, wall-clock timestamp or Matplotlib version is
stored. Matplotlib is not an MVP dependency.

`environment.commit` is not revalidated against git ancestry in the MVP. Check mode pins the
recomputed value to the committed value before comparing the rest, so a committed summary remains
checkable after `HEAD` advances. The commit is provenance, not a claim that the commit exists in
every clone.

### `FingerprintRecord`

| Field | Type | Rule |
|---|---|---|
| `historical` | string | Exactly `7c16ab39607d68a66bc2f4ac321933f64221d62980119ea780af5abf2a99f4e2` |
| `recipe` | string | Exact recipe text defined below |
| `recipe_version` | string | Exactly `historical-v1` |
| `provenance` | enum | Exactly `local_reconstruction` |
| `computed` | string | 64 lowercase hex characters |
| `matches` | bool | Exactly `true` in canonical output |
| `historical_file_count` | integer | Exactly `677` |
| `historical_total_bytes` | integer | Exactly `13,135,474` |
| `current_file_count` | integer | Count of regular files in the current `data/` tree |
| `current_total_bytes` | integer | Sum of current regular-file sizes |
| `status` | enum | Exactly `match` in canonical output |

The fixed `recipe` value is:

```text
regular files under data/ (no symlinks), sorted by POSIX relative path; for each: UTF-8 path + NUL + raw 32-byte SHA-256 of content; no trailing NUL/newline; lowercase hex
```

A fingerprint mismatch is not a `FingerprintRecord` outcome. The audit prints the historical and
computed hashes plus both historical and current counts to stderr, exits `2`, and writes no
canonical output. The historical constants are never replaced.

## 3. Inventory and annotation records

### `InventoryRecord`

`frame_list_count`, `frame_count` and `label_dir_count` are `60`; `instance_frame_count` is
`46`; `semantic_only_frame_count` is `14`; `frames` contains 60 `FrameRecord` values in
`frame_list.json` order.

`annotation_integrity` records the success-only structural checks:

| Field | Type | Rule |
|---|---|---|
| `semantic_values` | list[integer] | Exactly `[0, 2]` |
| `colour_mapping` | object | `normal: [0,0,0]`, `anomaly: [255,69,0]` |
| `colour_mapping_valid` | bool | `true`; only the declared colours appear |
| `instance_class_id` | integer | `2` for every instance |
| `instance_ids_contiguous` | bool | `true`; values are contiguous `1..N` |
| `label_files_complete` | bool | `true`; no missing or orphan label directory |
| `frame_decodable` | bool | `true`; every frame decodes as RGB 1280×720 |

An invalid annotation is a hard failure before `AuditResult` assembly, so these are success-only
constraints, not a way to serialize a broken input.

### `FrameRecord`

| Field | Type | Rule |
|---|---|---|
| `frame_name` | string | Basename from `frame_list.json`, ends `.webp` |
| `frame_path` | string | Canonical data-relative path `frames/<frame_name>` |
| `width` | integer | 1280 |
| `height` | integer | 720 |
| `mode` | string | `RGB` |
| `frame_sha256` | string | Raw file digest |
| `label_dir` | string | Canonical `frames/<stem>.labels` |
| `annotation_kind` | enum | `instance` or `semantic_only` |

`frame_path` and `label_dir` are logical paths relative to the data root, not absolute paths.
Temporary data roots therefore do not leak into committed bytes. Exactly 60 frames are present,
in frame-list order, with no duplicate name, missing label directory or orphan label directory.

### `InstanceSemanticRecord`

| Field | Type | Rule |
|---|---|---|
| `frames_checked` | integer | 46 |
| `frames_exact_match` | integer | 46 |
| `frames_mismatched` | integer | 0 |
| `mismatched_frames` | list[string] | Empty |
| `extra_instance_pixels` | integer | 0 |
| `missing_instance_pixels` | integer | 0 |
| `semantic_only_frames_excluded` | integer | 14 |
| `definition` | string | `union(instance values 1..N) == semantic value 2, per instance frame` |

For every instance-annotated frame, build the union of instance-mask pixels with values `1..N`
and compare it with semantic-mask pixels equal to `2`. The 14 semantic-only frames are excluded.
A mismatch prints each affected frame with its extra and missing pixel counts, exits `2`, and
writes no JSON or report. The audit never edits either mask.

## 4. Coverage, categories and object scale

### `CoverageRecord`

| Field | Type | Rule |
|---|---|---|
| `total_anomaly_pixels` | integer | Sum over 60 frames |
| `total_pixels` | integer | 55,296,000 |
| `pooled_fraction` | number | Exactly 0.09849561 |
| `pooled_percent` | number | Exactly 9.849561 |
| `minimum_percent` | number | Exactly 0.374674 |
| `maximum_percent` | number | Exactly 42.328559 |
| `median_percent` | number | Exactly 6.622938 |
| `below_one_percent` | list[string] | Exactly six sorted frame names |
| `per_frame` | list[`FrameCoverage`] | 60 entries in frame-list order |
| `definitions` | map[string]string | Required keys below |

`FrameCoverage`: `frame_name`, `anomaly_pixels`, `total_pixels` (`921600`), `fraction` and
`percent`. Values are serialized at six decimal places.

`definitions` requires exactly these keys, each with a non-empty formula/predicate:

- `pooled_fraction`: total anomaly pixels / total pixels over all 60 frames;
- `per_frame_fraction`: anomaly pixels / (1280 × 720);
- `percent`: 100 × fraction;
- `median`: median of the 60 per-frame fractions;
- `below_one_percent`: per-frame percent < 1.0.

### `CategoryRecord`

`counts` has exactly `animals`, `obstacles`, `cones`, `lost_tires` and `vehicle`, with baseline
counts `31`, `15`, `8`, `3` and `3`; `total_frames` is `60`; `classification` is exactly
`object_category_not_scene`. A prefix is not a scene ID, split unit or source group.

### `ScaleRecord`

| Field | Type | Rule |
|---|---|---|
| `roi_area_below_1024` | integer | 35 |
| `both_dimensions_below_32` | integer | 20 |
| `either_dimension_below_32` | integer | 46 |
| `median_roi_equivalent_square_px` | number | 86.7 |
| `median_roi_width_px` | number | 85.0 |
| `median_roi_height_px` | number | 107.0 |
| `median_mask_equivalent_square_px` | number | 51.2 |
| `denominator` | integer | 201 |
| `definitions` | map[string]string | Required keys below |

`definitions` requires exactly:

- `roi_area`: `(x1 - x0) × (y1 - y0)` using half-open ROI extents;
- `both_dimensions_below_32`: `width < 32 and height < 32`;
- `either_dimension_below_32`: `width < 32 or height < 32`;
- `roi_equivalent_square`: `sqrt(ROI area)`;
- `roi_bounding_box`: median ROI width and height;
- `mask_equivalent_square`: `sqrt(count of nonzero instance-mask pixels)`.

The definitions are computed by the audit and quoted by the renderer; the report must not choose
one small-object definition as the only truth.

## 5. Mapping, ROI and duplicates

### `MappingRecord`

`frames_checked` is `46`, `frames_agreeing` is `35`, `frames_disagreeing` is `11`,
`disagreeing_frames` is the complete sorted list, and `mismatches` contains objects with
`frame_name`, `mask_value`, `index_position` and `index_id`. `existing_test_check` is an object
with `name = "max(mask) == len(instances)"` and `passes = true`; it records the weaker existing
check without promoting it to the order mapping.

The order mapping compares mask value `k` with `instances[k-1].id`. A frame agrees only when
every value matches. The audit does not renumber masks or choose a different interpretation.

### `RoiRecord`

| Field | Type | Rule |
|---|---|---|
| `instances_checked` | integer | 201 |
| `out_of_bounds` | integer | 11 |
| `non_tight` | integer | 17 |
| `centroids_inside` | integer | 201 |
| `out_of_bounds_instances` | list[`AffectedInstance`] | At least the 11 baseline items |
| `non_tight_instances` | list[`AffectedInstance`] | At least the 17 baseline items |
| `definitions` | map[string]string | Required keys below |

`AffectedInstance` has `frame_name` and `mask_value`.

`definitions` requires exactly:

- `out_of_bounds`: `x0 < 0 or y0 < 0 or x1 > 1280 or y1 > 720`, half-open extents;
- `non_tight`: pixel box not strictly inside the half-open ROI:
  `bx0 < x0 or by0 < y0 or bx1 >= x1 or by1 >= y1`;
- `centroid_containment`: `0 <= (bx0+bx1)/2 < 1280` and
  `0 <= (by0+by1)/2 < 720`.

A ROI ending exactly at 1280 or 720 is inside. The audit never clips or rewrites a ROI.

### `DuplicateRecord`

`exact_pairs` and `decoded_pairs` are lists of frame pairs; `dhash_pairs` is a list of pairs with
a Hamming `distance`. `dhash_method` is exactly:

```text
9x8 grayscale dHash, 64 bits; Hamming distance <= 6
```

`limitations` is a non-empty list stating that the absence of reported pairs is method-limited,
not proof that no near-duplicates exist.

## 6. Credits, licensing and provenance

### `CreditRecord`

| Field | Type | Rule |
|---|---|---|
| `entries` | list[`CreditEntry`] | One per frame, 60 |
| `coverage` | integer | 60 |
| `missing_entries` | list[string] | Empty on the accepted checkout |
| `missing_licence_tokens` | list[string] | 24 frames, sorted |
| `missing_source_urls` | list[string] | Four obstacles12 frames |
| `source_groups` | list[`SourceGroup`] | Four groups covering 13 frames |
| `annotation_licence_claim` | string | `CC BY-SA 4.0` |
| `annotation_licence_sources` | list[string] | At least `data/credits.txt` and `docs/dataset.md` |
| `annotation_licence_terms_url` | string | Terms URL recorded in the credits |
| `code_licence` | string | `MIT` |
| `code_licence_source` | string | `LICENSE` |
| `code_licence_scope` | string | `source code; data and annotations excluded` |
| `legal_conclusion` | string | `not_made` |

`CreditEntry` fields: `frame_name`, `credit_text`, `licence_tokens` (list), `source_url`
(nullable) and `attribution`. `source_url` is the last non-`creativecommons.org` URL in the
credit block, in file order; a block with none yields `null`.

`SourceGroup` fields: `group_id`, `source_url` (nullable), `frames` and `frame_count`. Source
groups are attribution groups, not scenes.

The annotation and code licence claims are `documented_local`, not independently verified. A
missing per-image token remains `unresolved`; it is not evidence that the image is unlicensed.
`legal_conclusion` is always `not_made`.

### `ProvenanceRecord`

| Field | Type | Rule |
|---|---|---|
| `citation` | string | Lis et al., ICCV 2019 local citation |
| `release_identifier` | null | No local release/version/checksum identifier |
| `upstream_status` | enum | `upstream_unverified` |
| `scene_identity` | enum | `unresolved` |
| `filename_prefix_is_scene_id` | bool | `false` |
| `local_attribution_is_redistribution_proof` | bool | `false` |
| `normal_road_source_selected` | bool | `false` |
| `unresolved_items` | list[`UnresolvedItem`] | At least the ADR-0010 item |
| `p0_status` | map[string]string | P0-1 through P0-4, each `open` |
| `g10_status` | string | `open` |

`UnresolvedItem`: `item_id`, `statement`, `evidence_class` (exactly `unresolved`), `source`
and `status` (exactly `open`). The ADR-0010 item is:

```text
item_id: adr-0010-threshold-contradiction
statement: ADR-0010 leaves the threshold contradiction unresolved.
evidence_class: unresolved
source: docs/adr/0010-model-lineup-and-evaluation-contract.md
status: open
```

The item is reported, never reworded into a decision. P0-1 through P0-4 and G10 remain open.

## 7. Claims, documented comparisons and limitations

### `Claim`

| Field | Type | Rule |
|---|---|---|
| `claim_id` | string | Stable identifier, e.g. `coverage.pooled` |
| `text` | string | Report sentence or table caption |
| `evidence_class` | enum | `computed_local`, `documented_local`, `upstream_unverified`, `unresolved` |
| `value` | any | Reported scalar/object |
| `definition` | string or null | Formula or scope |
| `source` | string or null | File, ADR or documentation reference |

Every report numeric/table statement maps to a `Claim` or a typed field referenced by one. The
report includes a claim-classification appendix from this list.

### `DocumentedClaim`

Fields: `claim_id`, `documented_text`, `documented_source`, `computed_value` (string),
`computed_definition` and `treatment` (`report_both`, `report_gap` or `mark_unresolved`).
Baseline entries cover coverage rounding, 87 × 87/35 small objects, filename prefixes as scenes,
per-image licence completeness, benchmark folds and instance-ID equality. The audit never
rewrites the source document.

### `Limitation`

Fields: `limitation_id`, `statement`, `evidence_class`, `source` (nullable). Baseline limitations
include unverified visual registration, method-limited duplicate checks, attribution-derived
source groups, upstream-unverified provenance, missing per-image licence tokens and the
`environment.commit` provenance caveat.

## 8. Report and output behavior

The report is not a persisted object. `render_report(validated_summary: dict,
source_json_sha256: str)` receives only a schema-valid summary and formats it. It must not load
images, recompute a statistic or add a value absent from the JSON except the source JSON digest
itself.

Canonical outputs:

| Path | Role |
|---|---|
| `docs/validation/roadanomaly-eda.json` | Authoritative summary |
| `docs/validation/roadanomaly-eda.md` | Derived report with all 10 required sections |

The JSON does not contain the report hash. The report contains the validated JSON SHA-256. No
output manifest, readiness report, ledger, figure, overlay or artifact root exists in the MVP.

### Output policy

- `--output-root` must exist and be a directory.
- Inside the repository, only `docs/validation` is an allowed output root. Test runs use a
  temporary directory outside the repository.
- Only `roadanomaly-eda.json` and `roadanomaly-eda.md` may be created, plus their temporary
  siblings `roadanomaly-eda.json.tmp` and `roadanomaly-eda.md.tmp`.
- No subdirectory, figure, overlay, ledger, readiness report, split, class map or manifest may be
  created.
- A normal failure before replacement removes temporary files and leaves the old pair unchanged.
  Replacements are per-file atomic. A crash or a failure of the second replacement can leave a
  mixed pair; JSON remains authoritative and check mode detects a report whose source digest or
  bytes do not match. No journal or rollback machinery is added.

## 9. Extensions (not in this schema)

- **EXT-01 visual overlays and review ledger**: future fields and files, not present here.
- **EXT-02 aggregate figures**: future rendering from validated JSON, not present here.
- **EXT-03 normal-road readiness gate**: future `NR-01`–`NR-13` report, not present here.

Extensions must not add fields to the MVP schema without a separately approved change.

## 10. Validation summary

| Entity group | Required checks |
|---|---|
| Fingerprint | historical match, 677/13,135,474 historical counts, current counts, deterministic recomputation, drift exit `2` with no output |
| Inventory | 60 frames, 60 labels, 46 instance, 14 semantic-only |
| Integrity | dimensions, RGB, semantic values, colour mapping, contiguous instance IDs, `cls=2` |
| Instance/semantic | 46/46 exact, 0 extra, 0 missing, 14 excluded; mismatch is exit `2` with no output |
| Coverage | 9.849561 pooled, 0.374674–42.328559, 6.622938 median, six sub-1 % frames, five definitions |
| Categories | 31/15/8/3/3, object-category classification |
| Scale | 35/20/46 and 86.7/85.0/107.0/51.2 with six definitions |
| Mapping | 35/46 agree, 11/46 disagree, complete lists |
| ROI | 11/201 out-of-bounds, 17/201 non-tight, 201/201 centroids, complete lists, three definitions |
| Duplicates | exact, decoded and dHash methods with stated limits |
| Credits | 60 entries, 24 missing tokens, four source groups/13 frames, one group without URL |
| Licensing | annotation and code claims, sources, `legal_conclusion: not_made` |
| Provenance | upstream-unverified, cycle-free unresolved item, P0/G10 open |
| Claims | every report numeric/table statement evidence-classified |
| Report | 10 sections, source JSON digest, byte-identical re-render |
| Output | exactly two files, temp cleanup, normal failure leaves old pair, mixed pair detected by check |
| Schema | Draft 2020-12 meta-validation and generated-summary validation |
| Read-only | `data/`, protected docs and ADRs unchanged; no notebook statistics |
