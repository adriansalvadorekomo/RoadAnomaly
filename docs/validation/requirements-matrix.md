# Requirements traceability matrix

> Snapshot: **2026-10-19** · branch `main` · base `d237a85`.
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
| V1.1 | Complete code review | `main` has three commits and no pull request or review history. | `.github/PULL_REQUEST_TEMPLATE.md` (process only) | `missing` |
| V1.2 | Individual contribution and oral explanation | Every CODEOWNERS path routes to `@adriansalvadorekomo`; workstreams M1–M6 are unassigned. | `.github/CODEOWNERS`, README §Team | `missing` |
| V1.3 | Dataset comprehension | Verified 60 frames, 201 instances, 46 instance-annotated directories, 14 semantic-only directories, 9.8 % coverage; six integrity tests pass. No EDA notebook exists. | `README.md` §The dataset, `tests/dataset/test_dataset_integrity.py`, `data/readme.md` | `in progress` |
| V1.4 | At least three general models | 0 of 3 implemented; `dl/models/` contains only `.gitkeep`. The three families are specified. | `docs/adr/0002-three-model-families.md`, `dl/models/` | `missing` |
| V1.5 | One specific model per two members | Six members imply three specific models; M2/M3/M4 are defined but unassigned and empty. | `README.md` §Team, `dl/README.md` | `missing` |
| V1.6 | Classification, anomaly detection and segmentation objectives | Objectives are stated; no model implements them. | `README.md` §Methodology, ADR-0002 | `missing` |
| V1.7 | Model comparison and selected-model deployment | No checkpoints, results, API or container exists. | `README.md` §Results, `docs/experiments/` | `blocked` on V1.4–V1.6 |
| V1.8 | XAI implementation and justification | No XAI code, ADR or roadmap entry. A repository-wide search finds no Grad-CAM, SHAP, LIME or saliency reference. | none — gap G1 | `blocked` on a trained model; method undecided |

## Validation 2 — Commercial (40 %, W10)

| ID | Requirement | Evidence today | File / document | Status |
|---|---|---|---|---|
| V2.1 | Introduction | No commercial report exists. | none | `missing` |
| V2.2 | General context | No commercial report exists. | none | `missing` |
| V2.3 | Existing solutions | No survey or comparison exists. | none | `missing` |
| V2.4 | Deployed solutions | No survey or comparison exists. | none | `missing` |
| V2.5 | Problem statement | The operational problem is written for a technical audience. | `README.md` §The problem | `in progress` |
| V2.6 | Methodology | The evaluation protocol and model families are decided. | ADR-0001, ADR-0002, README §Methodology | `in progress` |
| V2.7 | Proposed solution | The target architecture is documented; nothing is deployed. | `README.md` §Target architecture, `docs/architecture/`, ADR-0003, ADR-0004, ADR-0005, ADR-0006 | `in progress` |
| V2.8 | Work completed | The current state is recorded honestly, but there is no report chapter. | `README.md` §Current architecture, §Project status | `in progress` |
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
| Technical (W9) | 0 | 1 | 5 | 2 | 8 |
| Commercial (W10) | 0 | 4 | 9 | 2 | 15 |
| **Both** | **0** | **5** | **14** | **4** | **23** |

The zeros are the honest result at this commit: the repository has a verified
dataset, a test harness and documentation, but no model, service or commercial
deliverable yet.

## Gaps that need a decision, not just work

| ID | Gap | Consequence |
|---|---|---|
| G1 | No XAI method is chosen, and XAI is not in ADR-0002 or the roadmap | V1.8 cannot start even after a model lands; the method and its justification must be recorded first |
| G2 | No EDA notebook (`dl/notebooks/01_dataset_eda.ipynb`) | Dataset comprehension stays `in progress` even though the facts are verified |
| G3 | No trained model of any family | Blocks V1.4–V1.8, the results table and the demo |
| G4 | No metric implementation or experiment record | Any number would be untraceable; the results table must stay empty |
| G5 | No API, frontend or container files | Blocks deployment, the teaser and the commercial demo |
| G6 | No per-member ownership or GitHub handles | Blocks V1.2 and meaningful CODEOWNERS routing |
| G7 | No commercial artefacts (BMC, 4Ps, penetration, brand, report) | Validation 2 is almost entirely `missing` |
| G8 | No Kubernetes manifests, Argo CD application or Vercel project | The deployment target is documented in ADR-0004 but not implemented |
| G9 | CD image, smoke-test and report jobs are gated on missing files | Expected until those files land; not a failure, but not a deployment either |

## How to update

1. Change a row only when the evidence file or command exists.
2. Record the command output or the file path in the evidence column.
3. Recompute the summary counts.
4. If a requirement moves to `implemented`, add the verification command to the
   final report and, when relevant, to `docs/experiments/`.
