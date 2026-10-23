# Contract: visual-review ledger (post-MVP extension)

**Feature**: `003-dataset-understanding` · **Version**: 1.0 · **Status**: Extension, not MVP

## Status

This contract documents a future visual-review extension. It is **not** part of the MVP schema,
tasks, report, CLI, tests or acceptance. The MVP audits annotation structure numerically; it does
not generate overlays and does not claim visual registration. A future approved change must add
its own schema fields, report sections and tests without weakening the core audit.

## Purpose

An overlay is generated evidence; a review is human evidence. A future ledger keeps generation
state and review state separate so a report can say exactly how many overlays were generated and
how many have a recorded disposition.

Future paths (not created by the MVP):

```text
docs/validation/roadanomaly-eda-visual-review.csv   # committed ledger
artifacts/dataset-understanding/overlays/           # Git-ignored overlays
```

## Rows

Exactly 106 rows:

- 60 `semantic` rows, one per frame;
- 46 `instance` rows, one per instance-annotated frame.

Rows sort by `kind` (alphabetically, so `instance` before `semantic`) then `frame_name`. Row
identity is `overlay_id`:

```text
instance:<frame_name>
semantic:<frame_name>
```

## Columns

| Column | Required | Rule |
|---|---|---|
| `overlay_id` | yes | Unique, stable identity above |
| `kind` | yes | `semantic` or `instance` |
| `frame_name` | yes | One of the 60 frame basenames |
| `overlay_path` | yes | Repository-relative path under the overlay root |
| `overlay_sha256` | yes | 64 lowercase hex characters |
| `overlay_width` | yes | Positive integer |
| `overlay_height` | yes | Positive integer |
| `generation_state` | yes | `generated` or `missing` |
| `generation_commit` | yes | Full source commit that generated the overlay |
| `audit_fingerprint` | yes | Historical fingerprint used for the run |
| `review_status` | yes | `not_reviewed` or `reviewed` |
| `disposition` | reviewed only | `aligned`, `minor_boundary_disagreement`, `major_misalignment` or `uncertain` |
| `reviewer` | reviewed only | Non-empty reviewer identity |
| `review_date` | reviewed only | ISO `YYYY-MM-DD` |
| `review_commit` | reviewed only | Commit reviewed against |
| `attribution` | yes | Credit line carried by the overlay caption |

For `not_reviewed` rows, the four review-only fields are empty. For `reviewed` rows, all four are
non-empty and `review_status` agrees with them. CSV is UTF-8, RFC 4180 quoting, LF, one fixed
header, no index column and no timestamp other than the reviewer-supplied date.

## Future generation and merge policy

1. **No ledger**: seed 106 rows, all `generated`/`not_reviewed`, with generation commit,
   fingerprint and attribution.
2. **Existing ledger**: parse and validate the header, unique IDs, 106 rows, overlay hashes and
   state. Refresh unreviewed rows. Preserve a reviewed row when its overlay hash, fingerprint and
   source frame match.
3. **Reviewed hash drift**: a reviewed row whose overlay hash changed is a hard failure. The old
   disposition is not silently moved to the new overlay; the reviewer must inspect and record a
   new disposition.
4. **Missing row**: an existing overlay without a ledger row is an error. Do not append over a
   human review file without an explicit review decision.
5. **Missing overlay**: `generation_state` becomes `missing` and generation fails with the
   expected path. It is never reported as reviewed.
6. **Check mode**: validate structure, hashes, reviewed fields and counts; write nothing; do not
   require ledger bytes to equal a fresh seed.

## Registration claim

A future report may set `registration_claim_allowed` only when all 106 overlays have a valid
reviewed disposition, reviewer, date, commit and fingerprint. Until then it must say visual
registration is **not verified** and must not infer alignment from dimensions, palette checks or
image similarity. Disagreement is data, not a failure to average away.

## Review workflow (future)

1. Generate overlays and seed the ledger.
2. Open each overlay at full resolution.
3. Compare anomaly pixels with the visible object and record exactly one disposition.
4. Fill reviewer, review date and review commit; keep the overlay hash and fingerprint unchanged.
5. Run check mode to validate the ledger and hashes.
6. Re-run generation to refresh the report counts; reviewed rows must survive.

## Rubric (fixed before review)

| Disposition | Meaning |
|---|---|
| `aligned` | The anomaly mask follows the visible anomalous object within normal annotation tolerance |
| `minor_boundary_disagreement` | The object is identifiable, but the mask has a local boundary or small missed/extra region |
| `major_misalignment` | The mask does not identify the intended object, or a large part is displaced |
| `uncertain` | The reviewer cannot decide from the overlay; uncertainty stays visible |

The rubric must not be changed after seeing a difficult frame without recording a new contract
version.

## Attribution

Each overlay carries the credit line for its frame. The ledger repeats it so a hash and its
attribution travel together. A future implementation must reuse the single credit parser and must
not treat local attribution as redistribution proof. Missing credit attribution is an input
failure, not an empty caption.

## Integration requirements

A future extension must update the JSON Schema, data model, report contract, tasks and tests in
one approved change. It must not add overlay fields to the MVP schema retroactively, must not
make the MVP check mode depend on Git-ignored files, and must not block the core audit on human
review.
