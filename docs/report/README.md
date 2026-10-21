# Report outline

Owner: **M6** assembles, everyone writes their own section. The Quarto source
will live in this directory, rendered to PDF/HTML and published to GitHub Pages
by CD.

Target: **roughly 16 pages** plus figures. The module grades problem statement,
methodology, results, and critical analysis — so the failure analysis gets real
space, not the appendix.

| § | Section | Pages | Owner | Content |
|---|---|---|---|---|
| 1 | Introduction | 1 | M1 | The operational problem: closed-set perception meets open-set reality |
| 2 | Dataset | 2 | M1 | The verified table from the README, category balance, the scale histogram, the semantic-only caveat, licensing |
| 3 | Methodology and protocol | 2 | M1 | CRISP-DM phases (ADR-0007), ADR-0001 in prose, selection vs held-out scoring, and what the protocol costs |
| 4 | Methods | 3 | M2 M3 M4 | Autoencoder reconstruction error, U-Net, DeepLabV3+; normal-road labels and MSP anomaly score |
| 5 | Metrics | 1 | M4 | Common binary-mask metrics (P/R/F1/IoU/Dice), complementary diagnostics, why F1 equals Dice, AUPRO cap and HD95 policy |
| 6 | Results | 3 | all | Normal-road selection table separately from RoadAnomaly held-out scores; per-frame distribution; worst frames |
| 7 | Ablations | 1.5 | M2–M4 | Threshold sensitivity, backbone choice, input resolution; zero-shot vs threshold-tuned |
| 8 | Explainability | 1 | M2–M4 | Seg-Grad-CAM, Integrated Gradients, error maps, faithfulness checks, examples and limits |
| 9 | Discussion | 1.5 | all | What worked, what did not, and the failure taxonomy |
| 10 | Conclusion | 0.5 | all | What we would do with another month |
| A | Reproducibility | 1 | M5 | Commands, seeds, hardware, environment, the artefact trail |

## Rules

- **Every number in the report traces to a file in `docs/experiments/`.** No
  exceptions, no numbers typed from memory or copied from a notebook cell.
- **Selection and held-out scoring are never merged.** The model choice is
  justified on normal-road validation; RoadAnomaly is reported as zero-shot and
  separately as threshold-tuned. A regression fitted on RoadAnomaly is a bug,
  not an ablation.
- **XAI is a method and a justification, not a screenshot.** The methods are
  fixed in ADR-0011, but the section must state that V1.8 is in progress until
  artefacts and faithfulness checks exist. Never present an unverified heatmap.
- **Limitations are stated before they are asked about.** A report that names
  its own weaknesses is stronger than one that has them extracted in review.
- **Data figures are generated, not screenshotted.** Plot scripts live with the
  experiment that produced the data. Architecture diagrams are rendered from
  `docs/architecture/workspace.dsl`, never hand-edited.
- **Cite the dataset paper** (Lis et al., ICCV 2019) and keep image attribution
  with every figure that shows a frame — the annotations are CC BY-SA 4.0.

## Commercial deliverables (Validation 2)

The commercial validation (40 %, W10) is a separate deliverable from the
technical report. It is tracked here so the two do not blur together. Statuses
follow [`docs/validation/requirements-matrix.md`](../validation/requirements-matrix.md).

| Deliverable | Source material today | Status |
|---|---|---|
| Introduction and general context | Standalone preliminary Business Understanding report ([TeX](Buisness%20Understanding%20report.tex), [PDF](Buisness%20Understanding%20report.pdf)); not yet integrated into the commercial report | `in progress` |
| Existing/deployed solutions | No survey or comparison yet | `missing` |
| Methodology, proposed solution, work completed | ADR-0001/0003/0004/0007/0008/0009/0010/0011/0012 and the README status sections | `in progress` |
| Business Model Canvas | none | `missing` |
| Marketing Mix (4Ps) | none | `missing` |
| Market penetration strategy | none | `missing` |
| Charts, logo and flyer | none | `missing` |
| Conclusion | none | `missing` |
| 45-second commercial teaser | Requires a working demo | `blocked` |
| Complete commercial report | Requires the sections above | `blocked` |

The standalone Business Understanding report is preliminary and does not
fulfil the complete commercial deliverable. It predates ADR-0010 and ADR-0011:
its model roadmap and metric list are historical and are not the current
contract. This table tracks the commercial deliverable and must be updated from
evidence like every other status in the repository.

The format of the complete commercial report (slides, PDF, or both) is not
decided yet.
