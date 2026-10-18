# `docs/` — decisions, experiments, report, diagrams

| Directory | Contents |
|---|---|
| `adr/` | Architecture and experiment decisions with the reasoning (start with [0001](adr/0001-evaluation-only-benchmark.md)) |
| `experiments/` | One file per run set: what was run, with which config, and what came out |
| `report/` | The technical report (Quarto → PDF/HTML, published to Pages by CD) |
| `assets/` | Diagram source: `architecture.json` (archify spec) and the generated `architecture.html` |

## Experiment log convention

Every run set gets one file, `docs/experiments/NNNN-short-name.md`:

```markdown
# 0007 — Resynthesis, threshold sweep

- Date: 2026-10-29
- Commit: abc1234
- Config: dl/configs/resynthesis.yaml
- Hardware: Colab T4, 41 min
- Command: make train CONFIG=dl/configs/resynthesis.yaml

## What changed
One paragraph. One variable.

## Results
| Model | IoU | F1 | AUPRC | FPR@95 |
|---|---|---|---|---|
| ... | | | | |

## What this means
Including the result that disagrees with the hypothesis.
```

A metric in the README that no experiment file supports should be treated as a
bug. The pull request template asks about this explicitly.

## Diagrams

`assets/architecture.json` is the source of truth for the architecture diagram;
`architecture.html` and the PNGs in `/assets` are generated from it. Regenerate
with the [archify](https://github.com/tt-a1i/archify) skill rather than editing
the HTML by hand — the HTML is a build artifact.
