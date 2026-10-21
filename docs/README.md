# `docs/` — decisions, experiments, report, diagrams

| Directory | Contents |
|---|---|
| `adr/` | Architecture and experiment decisions with the reasoning (start with [0001](adr/0001-evaluation-only-benchmark.md); methodology is [0007](adr/0007-crisp-dm-methodology.md)) |
| `experiments/` | One file per run set: what was run, with which config, and what came out |
| `report/` | Technical report outline, commercial deliverable plan, and a standalone preliminary Business Understanding report (TeX/PDF) |
| `validation/` | Traceability matrix for the technical and commercial validations |
| `architecture/` | Structurizr C4 source, render script and committed C1/C2 PNGs |
| `metrics.md` | Normative metric contract; not an implementation |
| `xai.md` | XAI methods, faithfulness checks and evidence format; not an implementation |

## Experiment log convention

Every run set gets one file, `docs/experiments/NNNN-short-name.md`, copied from
[`experiments/0000-template.md`](experiments/0000-template.md). It records the
commit, config hash, command, seed, hardware, normal-road dataset manifest and
split hash, and artifact digest.

Results are split into two blocks that must not be merged:

- **Normal-road validation** — the only selection signal.
- **RoadAnomaly held-out** — zero-shot and threshold-tuned reported separately;
  never a promotion signal.

A metric in the README that no experiment file supports should be treated as a
bug. The pull request template asks about this explicitly.

## Diagrams

[`architecture/workspace.dsl`](architecture/workspace.dsl) is the single source
of truth for the C4 model. The committed C1 system-context and C2 offline-pipeline
PNGs are rendered from it into [`architecture/diagrams/`](architecture/diagrams/).
The model is target-state: the dataset and contract tests exist; models, metrics,
XAI, serving and deployment are planned.

Run `make architecture` (Java 21 + Chromium) to re-render; commit the PNGs and
`diagrams/manifest.json` with the DSL. Do not hand-edit the PNGs or add a second
architecture source. `tests/architecture/` enforces the semantic rules (no
benchmark-to-registry path, normal-road selection, XAI gate, metric/XAI contracts
and PNG dimensions), and CI validates the DSL with Structurizr.
