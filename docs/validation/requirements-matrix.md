# Requirements traceability matrix

> Snapshot: **2026-10-19** · branch `main` · base `9d6041f`.
> Update this file whenever a status changes; do not update it from memory.

Two validations are graded independently. This matrix maps every requirement to
the evidence that would satisfy it. **A README statement is not evidence.**
`implemented` requires a file or a command that proves the capability.

## Status definitions

| Status | Meaning |
|---|---|
| `implemented` | The artefact exists in this repository and the listed file or command verifies it. |
| `in progress` | Partial evidence exists; the deliverable is not complete. |
| `missing` | No artefact exists. Work can start; only capacity blocks it. |
| `blocked` | No artefact exists and a named dependency must land first. |

## Validation 1 — Technical (60 %, W9)

| ID | Requirement | Evidence today | File / document | Status |
|---|---|---|---|---|
| V1.1 | Complete code review | PR #3 merged at `9d6041f`, but no independent reviewer is recorded; the review history is still self/agent review. | `.github/PULL_REQUEST_TEMPLATE.md`, PR #3 | `in progress` |
| V1.2 | Individual contribution and oral explanation | Every CODEOWNERS path routes to `@adriansalvadorekomo`; workstreams M1–M6 are unassigned. | `.github/CODEOWNERS`, README §Team | `missing` |
| V1.3 | Dataset comprehension | Verified 60 frames, 201 instances, 46 instance-annotated directories, 14 semantic-only directories, 9.8 % coverage; six integrity tests pass. No EDA notebook exists. | `README.md` §4, `tests/dataset/test_dataset_integrity.py`, `data/readme.md` | `in progress` |
| V1.4 | At least three general models | 0 of 3 implemented; `dl/models/` contains only `.gitkeep`. The three families are specified. | `docs/adr/0002-three-model-families.md`, `dl/models/` | `missing` |
| V1.5 | One specific model per two members | Six members imply three specific models; M2/M3/M4 are defined but unassigned and empty. | `README.md` §Team, `dl/README.md` | `missing` |
| V1.6 | Classification, anomaly detection and segmentation objectives | Objectives and the three-family comparison are stated; no model implements them. | `README.md` §1 and §3, ADR-0002, ADR-0007 | `missing` |
| V1.7 | Model comparison and selected-model deployment | No checkpoints, results, API or container exists. | `README.md` §Results, `docs/experiments/` | `blocked` on V1.4–V1.6 |
| V1.8 | XAI implementation and justification | Placement and evidence format are recorded, but no method is chosen and no XAI code exists. Grad-CAM, occlusion, integrated gradients and saliency are named only as candidates. | `docs/adr/0009-xai-evaluation-gate.md`, `docs/architecture/README.md` §XAI | `blocked` on a trained model and a method decision (G1) |

## Validation 2 — Commercial (40 %, W10)

| ID | Requirement | Evidence today | File / document | Status |
|---|---|---|---|---|
| V2.1 | Introduction | No commercial report exists. | none | `missing` |
| V2.2 | General context | No commercial report exists. | none | `missing` |
| V2.3 | Existing solutions | No survey or comparison exists. | none | `missing` |
| V2.4 | Deployed solutions | No survey or comparison exists. | none | `missing` |
| V2.5 | Problem statement | The operational problem is written for a technical audience. | `README.md` §1 | `in progress` |
| V2.6 | Methodology | CRISP-DM, the evaluation protocol and the three-family comparison are decided; the report chapter is not written. | ADR-0001, ADR-0002, ADR-0007, README §3 | `in progress` |
| V2.7 | Proposed solution | The target architecture, promotion rule and XAI gate are documented; nothing is deployed. | `README.md` §3, `docs/architecture/`, ADR-0003–0009 | `in progress` |
| V2.8 | Work completed | The current state is recorded honestly, but there is no report chapter. | `README.md` §2 and §13 | `in progress` |
| V2.9 | Business Model Canvas | No canvas exists. | none | `missing` |
| V2.10 | Marketing Mix (4Ps) | No analysis exists. | none | `missing` |
| V2.11 | Market penetration strategy | No strategy exists. | none | `missing` |
| V2.12 | Charts, logo and flyer | No brand or communication artefact exists. | none | `missing` |
| V2.13 | Conclusion | No report exists. | none | `missing` |
| V2.14 | 45-second commercial teaser | No demo exists to film. | none | `blocked` on V2.7/V1.7 |
| V2.15 | Complete report | Neither the technical nor the commercial report exists. | `docs/report/README.md` (outline only) | `blocked` on results and V2.1–V2.13 |

## Summary

| Validation | `implemented` | `in progress` | `missing` | `blocked` | Total |
|---|---:|---:|---:|---:|---:|
| Technical (W9) | 0 | 2 | 4 | 2 | 8 |
| Commercial (W10) | 0 | 4 | 9 | 2 | 15 |
| **Both** | **0** | **6** | **13** | **4** | **23** |

The zeros are the honest result at this commit: the repository has a verified
dataset, test harnesses and documentation, but no model, service or commercial
deliverable yet. PR #3 is merged, but that is not the same as an independent
code review.

## Gaps that need a decision, not just work

| ID | Gap | Consequence |
|---|---|---|
| G1 | No XAI method is chosen. ADR-0009 fixes placement and the gate, but not the method. | V1.8 cannot start even after a model lands; the method and its justification must be recorded first |
| G2 | No EDA notebook (`dl/notebooks/01_dataset_eda.ipynb`) | Dataset comprehension stays `in progress` even though the facts are verified |
| G3 | No trained model of any family | Blocks V1.4–V1.8, the results table and the demo |
| G4 | No metric implementation or experiment record | Any number would be untraceable; the results table must stay empty |
| G5 | No API, frontend or container files | Blocks deployment, the teaser and the commercial demo |
| G6 | No per-member ownership or GitHub handles | Blocks V1.2 and meaningful CODEOWNERS routing |
| G7 | No commercial artefacts (BMC, 4Ps, penetration, brand, report) | Validation 2 is almost entirely `missing` |
| G8 | No Kubernetes manifests, Argo CD application or Vercel project | The deployment target is documented in ADR-0004 but not implemented |
| G9 | CD quality gate and immutable-digest publication are implemented in the workflow; image, smoke, promotion and report jobs are gated on missing files | Expected until those files land; not a failure, but not a deployment either |
| G10 | No normal-road release, scene list or split manifest is pinned | Phase 3 cannot be reproducible; any training run would lack a defensible train/validation boundary |

## How to update

1. Change a row only when the evidence file or command exists.
2. Record the command output or the file path in the evidence column.
3. Recompute the summary counts.
4. If a requirement moves to `implemented`, add the verification command to the
   final report and, when relevant, to `docs/experiments/`.
