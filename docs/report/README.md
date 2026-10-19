# Report outline

Owner: **M6** assembles, everyone writes their own section. Quarto source in
this directory, rendered to PDF/HTML and published to GitHub Pages by CD.

Target: **12–16 pages** plus figures. The module grades problem statement,
methodology, results, and critical analysis — so the failure analysis gets real
space, not the appendix.

| § | Section | Pages | Owner | Content |
|---|---|---|---|---|
| 1 | Introduction | 1 | M1 | The operational problem: closed-set perception meets open-set reality |
| 2 | Dataset | 2 | M1 | The verified table from the README, category balance, the scale histogram, the semantic-only caveat, licensing |
| 3 | Protocol | 1.5 | M1 | ADR-0001 in prose: why these 60 frames are evaluation-only, and what that costs |
| 4 | Methods | 3 | M2 M3 M4 | Autoencoder, resynthesis (with the deviations from Lis et al. and why), segmentation + MSP |
| 5 | Metrics | 1 | M4 | Definitions, why AUPRC is primary under 9.8 % coverage, the FPR@95 argument |
| 6 | Results | 3 | all | Main table, per-frame distribution, qualitative grid including the worst frames |
| 7 | Ablations | 1.5 | M2–M4 | Threshold sensitivity, backbone choice, input resolution |
| 8 | Discussion | 1.5 | all | What worked, what did not, and the failure taxonomy |
| 9 | Conclusion | 0.5 | all | What we would do with another month |
| A | Reproducibility | 1 | M5 | Commands, seeds, hardware, environment, the artefact trail |

## Rules

- **Every number in the report traces to a file in `docs/experiments/`.** No
  exceptions, no numbers typed from memory or copied from a notebook cell.
- **Limitations are stated before they are asked about.** A report that names
  its own weaknesses is stronger than one that has them extracted in review.
- **Figures are generated, not screenshotted.** Plot scripts live with the
  experiment that produced the data.
- **Cite the dataset paper** (Lis et al., ICCV 2019) and keep image attribution
  with every figure that shows a frame — the annotations are CC BY-SA 4.0.

## Commercial deliverables (Validation 2)

The commercial validation (40 %, W10) is a separate deliverable from the
technical report. It is tracked here so the two do not blur together. Statuses
follow [`docs/validation/requirements-matrix.md`](../validation/requirements-matrix.md).

| Deliverable | Source material today | Status |
|---|---|---|
| Introduction, general context, existing/deployed solutions | Nothing beyond the technical problem statement | `missing` (problem statement `in progress` in `README.md`) |
| Methodology, proposed solution, work completed | ADR-0001/0002/0003/0004 and the README status sections | `in progress` |
| Business Model Canvas | none | `missing` |
| Marketing Mix (4Ps) | none | `missing` |
| Market penetration strategy | none | `missing` |
| Charts, logo and flyer | none | `missing` |
| Conclusion | none | `missing` |
| 45-second commercial teaser | Requires a working demo | `blocked` |
| Complete commercial report | Requires the sections above | `blocked` |

No commercial artefact exists at this commit. This table is a plan, not a
claim, and it must be updated from evidence like every other status in the
repository.

The format (slides, PDF, or both) is not decided yet; do not create a
commercial subdirectory until the first artefact has a home.
