# Requirements traceability matrix

> Snapshot: **2026-10-21** · branch `docs/structurizr-c4-refactor` ·
> base `0f9d53f`. Update this file whenever a status changes; do not update it
> from memory.

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
| V1.1 | Complete code review | PRs #3–#5 are merged, but no independent reviewer is recorded; the review history is still self/agent review. | `.github/PULL_REQUEST_TEMPLATE.md`, PR #3–#5 | `in progress` |
| V1.2 | Individual contribution and oral explanation | Every CODEOWNERS path routes to `@adriansalvadorekomo`; workstreams M1–M6 are unassigned. | `.github/CODEOWNERS`, README §Team | `missing` |
| V1.3 | Dataset comprehension | Verified 60 frames, 201 instances, 46 instance-annotated directories, 14 semantic-only directories, 9.8 % coverage; six integrity tests pass. No EDA notebook exists. | `README.md` §4, `tests/dataset/test_dataset_integrity.py`, `data/readme.md` | `in progress` |
| V1.4 | At least three general models | 0 of 3 implemented; `dl/models/` contains only `.gitkeep`. ADR-0010 fixes autoencoder, U-Net and DeepLabV3+. | `docs/adr/0010-model-lineup-and-evaluation-contract.md`, `dl/models/` | `missing` |
| V1.5 | One specific model per two members | Six members imply three specific models; M2/M3/M4 are defined but unassigned and empty. | `README.md` §Team, `dl/README.md` | `missing` |
| V1.6 | Classification, anomaly detection and segmentation objectives | Objectives and the three-model comparison are stated; no model implements them. DeepLabV3+ and U-Net provide dense multi-class classification; there is no separate image-level classifier. | `README.md` §1 and §5, ADR-0010, ADR-0007 | `missing` |
| V1.7 | Model comparison and selected-model deployment | No checkpoints, results, API or container exists. | `README.md` §Results, `docs/experiments/` | `blocked` on V1.4–V1.6 |
| V1.8 | XAI implementation and justification | ADR-0011 selects the methods and faithfulness checks, and `docs/xai.md` fixes the evidence format. No XAI code, heatmap or faithfulness result exists. | `docs/adr/0011-xai-methods-and-faithfulness.md`, `docs/xai.md` | `in progress`; implementation gated on V1.4 |

## Validation 2 — Commercial (40 %, W10)

| ID | Requirement | Evidence today | File / document | Status |
|---|---|---|---|---|
| V2.1 | Introduction | A standalone preliminary Business Understanding report exists; it is not yet integrated into the commercial report. | `docs/report/Buisness Understanding report.pdf` | `in progress` |
| V2.2 | General context | Covered in the standalone preliminary Business Understanding report; the commercial report chapter is not yet integrated. | `docs/report/Buisness Understanding report.pdf` | `in progress` |
| V2.3 | Existing solutions | No survey or comparison exists. | none | `missing` |
| V2.4 | Deployed solutions | No survey or comparison exists. | none | `missing` |
| V2.5 | Problem statement | The operational problem is written for a technical audience. | `README.md` §1 | `in progress` |
| V2.6 | Methodology | CRISP-DM, the evaluation-only protocol and the three-model comparison are decided; the report chapter is not written. | ADR-0001, ADR-0007, ADR-0010, README §3 | `in progress` |
| V2.7 | Proposed solution | The target C4 context/offline pipeline, promotion rule and XAI gate are documented; nothing is deployed. | `README.md` §3, `docs/architecture/workspace.dsl`, ADR-0003–0012 | `in progress` |
| V2.8 | Work completed | The current state is recorded honestly, but there is no report chapter. | `README.md` §2 and §9 | `in progress` |
| V2.9 | Business Model Canvas | No canvas exists. | none | `missing` |
| V2.10 | Marketing Mix (4Ps) | No analysis exists. | none | `missing` |
| V2.11 | Market penetration strategy | No strategy exists. | none | `missing` |
| V2.12 | Charts, logo and flyer | No brand or communication artefact exists. | none | `missing` |
| V2.13 | Conclusion | No report exists. | none | `missing` |
| V2.14 | 45-second commercial teaser | No demo exists to film. | none | `blocked` on V2.7/V1.7 |
| V2.15 | Complete report | The standalone Business Understanding report is preliminary; no complete report is available. | `docs/report/README.md` (outline and preliminary report) | `blocked` on results and V2.1–V2.13 |

## Summary

| Validation | `implemented` | `in progress` | `missing` | `blocked` | Total |
|---|---:|---:|---:|---:|---:|
| Technical (W9) | 0 | 3 | 4 | 1 | 8 |
| Commercial (W10) | 0 | 4 | 9 | 2 | 15 |
| **Both** | **0** | **7** | **13** | **3** | **23** |

The zeros are the honest result at this commit: the repository has a verified
dataset, test harnesses and documentation, but no model, service or commercial
deliverable yet. PRs #3–#5 are merged, but that is not the same as an
independent code review.

## Gaps and dependencies

| ID | Gap | Consequence |
|---|---|---|
| G1 | **Resolved 2026-10-21.** ADR-0011 selects reconstruction-error maps, Integrated Gradients and Seg-Grad-CAM, with deletion/insertion and pointing-game checks. | Method no longer blocks V1.8; the implementation is gated on G3 |
| G2 | No EDA notebook (`dl/notebooks/01_dataset_eda.ipynb`) | Dataset comprehension stays `in progress` even though the facts are verified |
| G3 | No trained model of any family | Blocks V1.4–V1.8, the results table and the demo |
| G4 | No metric or XAI implementation and no experiment record; the contracts exist in `docs/metrics.md` and `docs/xai.md` | Any number would be untraceable; the results table must stay empty |
| G5 | No API, frontend or container files | Blocks deployment, the teaser and the commercial demo |
| G6 | No per-member ownership or GitHub handles | Blocks V1.2 and meaningful CODEOWNERS routing |
| G7 | No commercial artefacts (BMC, 4Ps, penetration, brand, report) | Validation 2 is almost entirely `missing` |
| G8 | No Kubernetes manifests, Argo CD application or Vercel project | The deployment target is documented in ADR-0004 but not implemented |
| G9 | CD quality gate and immutable-digest publication are implemented in the workflow; image, smoke, promotion and report jobs are gated on missing files | Expected until those files land; not a failure, but not a deployment either |
| G10 | No normal-road release, scene list or split manifest is pinned | Phase 3 cannot be reproducible; any training run would lack a defensible train/validation boundary |
| G11 | No separate image-level classifier; DeepLabV3+ provides dense multi-class prediction only | The classification objective is met at pixel level, not by an image label; state this explicitly in the defence |

## How to update

1. Change a row only when the evidence file or command exists.
2. Record the command output or the file path in the evidence column.
3. Recompute the summary counts.
4. If a requirement moves to `implemented`, add the verification command to the
   final report and, when relevant, to `docs/experiments/`.
