# `docs/` — decisions, experiments, report, diagrams

| Directory | Contents |
|---|---|
| `adr/` | Architecture and experiment decisions with the reasoning (start with [0001](adr/0001-evaluation-only-benchmark.md); methodology is [0007](adr/0007-crisp-dm-methodology.md)) |
| `experiments/` | One file per run set: what was run, with which config, and what came out |
| `report/` | The technical report (Quarto → PDF/HTML, published to Pages by CD) and the commercial deliverable plan |
| `validation/` | Traceability matrix for the technical and commercial validations |
| `architecture/` | Component and deployment documentation; `architecture.json` (archify spec) and the generated `architecture.html` / README PNGs |

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

`architecture/architecture.json` is the source of truth for the architecture
diagram; `architecture.html` and the PNGs in `/assets` are generated from it.
The spec follows the six CRISP-DM phases in
[ADR-0007](adr/0007-crisp-dm-methodology.md) and describes the **target**
architecture; the current-state diagram is the Mermaid block in
[`architecture/README.md`](architecture/README.md). Regenerate with the
[archify](https://github.com/tt-a1i/archify) skill rather than editing the HTML
by hand — the HTML is a build artifact. `tests/architecture/` enforces the
semantic rules (no benchmark-to-registry path, XAI present, six regions, PNG
dimensions).
