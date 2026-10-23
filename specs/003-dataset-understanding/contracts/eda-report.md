# Contract: EDA report

**Feature**: `003-dataset-understanding` · **Version**: 1.0 · **Scope**: MVP

## Purpose

The report is a deterministic rendering of the validated JSON summary. It does not load images,
recompute a statistic or introduce a value that is absent from the JSON. Its only added value is
the SHA-256 of the validated JSON bytes, which is the source digest.

Canonical path: `docs/validation/roadanomaly-eda.md`.

The report is canonical only after the JSON has passed `contracts/audit-summary.schema.json`.
A report rendered from an unvalidated object is invalid. The report does not contain its own hash
and the JSON does not contain the report hash.

## Required sections

The report contains exactly these headings, in this order:

1. **Scope and method** — benchmark-only scope, read-only rule, evidence classes, explicit
   statement that overlays, figures, visual review and normal-road readiness are post-MVP
   extensions and are not assessed here.
2. **Environment and reproduction** — the source commit, Python, NumPy, Pillow and `jsonschema`
   versions, audit version, `make data-audit` and `make data-audit-check`, and the canonical
   command rule. No Matplotlib or figure version is claimed.
3. **Fingerprint** — the exact recipe string, historical value, historical 677 files and
   13,135,474 bytes, computed value, current file/byte counts, `match` status and
   `local_reconstruction` provenance caveat. The current counts do not replace the baseline.
4. **Inventory and integrity** — 60 frames, 60 label directories, 46 instance-annotated and 14
   semantic-only frames, image dimensions/mode, semantic values, colour mapping and contiguous
   instance IDs with `cls=2`.
5. **Instance/semantic consistency** — the exact definition, 46 frames checked, 46 exact, 0
   mismatched, 0 extra instance pixels, 0 missing instance pixels and 14 semantic-only frames
   excluded. State that a mismatch is a hard exit-2 failure, not a report outcome.
6. **Coverage, categories and object scale** — pooled/per-frame/median coverage, the six sub-1 %
   frames, category counts labelled as object categories, and every scale field with its named
   definition.
7. **Instance mapping, ROI and duplicates** — 35/46 order agreement, 11/46 disagreement and the
   complete affected lists; 11/201 out-of-bounds ROIs, 17/201 non-tight boxes, 201/201 centroids
   and the half-open definitions; exact/decoded/dHash methods and their limits. List every
   affected frame/instance, not only the counts.
8. **Credits, licensing and provenance** — 60 credit entries, 24 missing per-image licence
   tokens, four source groups covering 13 frames (including the group without a URL), annotation
   `CC BY-SA 4.0`, code `MIT`, source paths, `legal_conclusion: not_made`, upstream
   `unresolved`/`upstream_unverified`, and the fact that local attribution is not redistribution
   proof.
9. **Documented claims, limitations and unresolved items** — every `DocumentedClaim` side by
   side with its computed value, definition and treatment; every `Limitation`; the
   `provenance.unresolved_items` list including the ADR-0010 threshold contradiction; and the
   statement that P0-1 through P0-4 and G10 remain open.
10. **Validation and output integrity** — schema validation, canonical command, source JSON
    SHA-256 labelled `computed_local`, the two-file output set, check mode, and the per-file
    replacement limitation. State that no class map, split, split hash, manifest, experiment
    record, figure, overlay, ledger or readiness report was created.

## Required statements

The report must state:

- the benchmark is evaluation-only and no model was fitted, selected, tuned, scored or promoted;
- the fingerprint match does not prove the original Stage 2 implementation byte layout;
- the audit is a local reconstruction and `environment.commit` is provenance, not a revalidated
  git ancestry claim;
- P0-1 through P0-4, G10 and the ADR-0010 threshold contradiction remain open;
- no class map, split, split hash, manifest or experiment record was created;
- the annotation and code licence statements are local documented claims, not legal advice;
- visual registration, overlays, figures, the review ledger and normal-road readiness are not
  assessed in the MVP and are not claimed as verified;
- the JSON is authoritative; the report is derived from validated JSON bytes;
- the two output files are replaced individually, so a crash between replacements can leave a
  mixed pair that check mode detects.

## Claims and parity

- Every numeric or table statement in the report maps to a JSON field or a `Claim` entry and
  displays its evidence class (`computed_local`, `documented_local`, `upstream_unverified` or
  `unresolved`) next to the value or in the claim appendix.
- Every `DocumentedClaim` in JSON appears in section 9 with the same `treatment`.
- Every credit/licensing claim in JSON appears in section 8.
- Every `provenance.unresolved_items` entry appears in section 9; the ADR-0010 item is never
  resolved or reworded into a decision.
- The report's source JSON SHA-256 equals the SHA-256 of the committed validated JSON bytes.
- The report re-rendered from the committed JSON is byte-identical to the committed report.

Matching headings alone is insufficient; the parity test walks values back to JSON.

## Format and determinism

Markdown is UTF-8 with LF endings and deterministic row/section order. It contains no wall-clock
timestamp, host-specific path or absolute workspace path. `environment.commit` is pinned by check
mode before comparison, so the report remains byte-identical after the evidence commit advances
`HEAD`.

## Out of scope

The report does not include visual overlays, overlay hashes, a review ledger, aggregate figures,
normal-road readiness criteria, source acquisition/ranking or any model/metric/threshold result.
Those are post-MVP extensions and must be specified separately.
