# Contract: normal-road readiness gate (post-MVP extension)

**Feature**: `003-dataset-understanding` · **Version**: 1.0 · **Status**: Extension, not MVP

## Status

This contract documents a future readiness gate. It is **not** part of the MVP schema, tasks,
report, CLI, tests or acceptance. The MVP does not select, survey, download, rank or recommend a
normal-road source. It records that no source is selected and that P0-1 through P0-4 and G10
remain open; it does not produce a readiness report.

A future approved change may implement the registry below under extension `EXT-03`. That change
must add its own schema fields, report section and tests without changing the benchmark audit
result or making the core check mode depend on a normal-road corpus.

## Purpose

The gate is a checklist, not a source selection. With no source selected, every criterion is
`unresolved` and no source is named. The registry records the concrete evidence a future source
would need and the P0/G10 dependency affected when the criterion is unresolved.

## Registry

| ID | Criterion | Evidence fields | Blocking |
|---|---|---|---|
| NR-01 | Gate is a checklist, not a source selection | `no_source_statement`, `no_candidate_survey`, `no_ranking_or_recommendation` | G10 |
| NR-02 | Source identity and pinning | `source_name`, `publisher`, `release_version`, `retrieval_url`, `retrieval_date`, `citation`, `immutable_identifier_or_checksum` | G10 |
| NR-03 | Licence terms | `licence_identifier`, `licence_terms_url`, `permitted_uses`, `prohibited_uses`, `attribution_requirements`, `image_terms`, `annotation_terms` | G10 |
| NR-04 | Image inventory and integrity | `image_count`, `format`, `dimensions`, `decodability`, `corruption_checks`, `duplicate_checks`, `near_duplicate_checks`, `exif_orientation_handling`, `hashes` | G10 |
| NR-05 | Normal-scene eligibility | `road_scene_domain`, `absence_of_anomalies`, `no_synthetic_insertions`, `no_roadanomaly_frames`, `exclusion_rules`, `not_tuned_on_benchmark` | G10 |
| NR-06 | Label evidence without deciding the contract | `labels`, `classes_or_ids`, `annotation_formats`, `label_resolution_alignment`, `ignore_void`, `label_provenance`, `semantic_supervision_evidence`, `normal_image_only_evidence`, `class_map_not_decided` | P0-1, G10 |
| NR-07 | Stable scene identity | `stable_scene_ids`, `scene_identity_evidence`, `not_filename_prefix_category_or_credit_group` | G10 |
| NR-08 | Leakage control | `scene_sequence_session_grouping`, `duplicate_detection`, `no_same_scene_across_groups` | G10 |
| NR-09 | Split protocol possible, not created | `scene_grouped_split_protocol_possible`, `no_split_hash`, `no_frame_assignment`, `no_split_files` | G10 |
| NR-10 | Manifest schema sufficiency | `manifest_schema_assessment`, `class_map_fields_present`, `label_hash_fields_present`, `no_schema_extension` | P0-1, G10 |
| NR-11 | Report completeness | `criterion_statuses`, `evidence_citations`, `blocking_map`, `all_unresolved_baseline` | P0-1, G10 |
| NR-12 | No benchmark overlap or benchmark-driven eligibility | `no_roadanomaly_overlap`, `not_used_for_eligibility`, `not_used_for_classes`, `not_used_for_splits` | G10 |
| NR-13 | No P0 resolution | `P0-1_open`, `P0-2_open`, `P0-3_open`, `P0-4_open`, `no_class_map`, `no_benchmark_authorization`, `no_threshold_protocol_resolution` | P0-1, P0-2, P0-3, P0-4, G10 |

NR-06, NR-10, NR-11 and NR-13 block P0-1. NR-13 also guards P0-2 through P0-4. G10 remains open
because no normal-road source, scene list or manifest exists.

## Baseline if implemented

- `source_selected` is `false` and `source_name` is `null`.
- Exactly 13 criteria are present, with no duplicates.
- Every criterion is `unresolved` and every `evidence` value is `null`.
- `all_unresolved` is `true`.
- `downloads`, `surveyed_sources`, `class_maps_created`, `split_files_created` and
  `manifests_created` are all `0`.
- P0-1 through P0-4 and G10 remain open.
- `manifest_schema_gap` records that class-map and label-hash fields are not yet specified.

An all-`unresolved` gate is a valid future outcome. It is not a failure and must not trigger a
data search.

## Status semantics

- `pass`: concrete evidence exists and satisfies the requirement.
- `fail`: concrete evidence exists and contradicts the requirement.
- `unresolved`: no source or insufficient evidence; the valid baseline when no source is selected.

No criterion may be marked `pass` from documentation alone. No candidate may be named, ranked or
recommended. The gate must not use the RoadAnomaly benchmark to choose normal-road scenes,
classes or splits.

## Required report statements if implemented

- “no source selected”;
- all `NR-01`–`NR-13` with status, evidence fields and blocking;
- every unresolved criterion needs the listed evidence;
- P0-1 through P0-4 and G10 remain open;
- the manifest-schema gap is flagged;
- zero downloads, surveyed sources, class maps, split files and manifests were created.

## Tests if implemented

- exact IDs `NR-01`–`NR-13`, no duplicates;
- all 13 statuses `unresolved`, all evidence `null`;
- `source_selected = false`, `source_name = null`, `all_unresolved = true`;
- all zero counters and open P0/G10 statuses;
- the blocking map above.

These tests are future work. The MVP does not claim readiness validation.
