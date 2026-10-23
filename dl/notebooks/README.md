# Notebooks — learning clients

The notebook suite is the **learning interface**. Official training, evaluation,
thresholding, export and XAI still run from `dl/` and the `make` targets. A
notebook may explain an idea, inspect an intermediate tensor, visualise a result
and run a controlled exercise; it may not become a second implementation.

The template is the central guided tour. The five specialized notebooks are
focused deep dives. `04_comparison` is not a separate notebook: comparison lives
in the template's end-to-end section and in the official evaluation output.

## Map

| Notebook | Role | Status | Primary `dl/` code |
|---|---|---|---|
| `template_road_anomaly.ipynb` | Central guided tour, ownership map, end-to-end comparison | **present**; legacy inline stubs being migrated | `dl/config.py`, `dl/data/`, `dl/models/`, `dl/training/`, `dl/evaluation/` |
| `road-anomaly-dataset-exploration.ipynb` | Scientific EDA over the canonical audit JSON; presentation client, not a second implementation | **present** | `dl/data/audit.py`, `docs/validation/roadanomaly-eda.json` |
| `01_dataset_eda.ipynb` | Dataset inventory, label audit, coverage, benchmark inspection | planned | `dl/data/` |
| `02_deeplabv3plus.ipynb` | DeepLabV3+ architecture, ASPP, transfer learning and diagnostics | planned | `dl/models/deeplabv3plus.py`, `dl/training/`, `dl/evaluation/` |
| `03_autoencoder.ipynb` | Autoencoder reconstruction, error maps and per-pixel aggregation | planned | `dl/models/autoencoder.py`, `dl/training/`, `dl/evaluation/` |
| `04_cnn_unet.ipynb` | CNN baseline versus U-Net, skip connections and segmentation diagnostics | planned | `dl/models/unet.py`, `dl/training/`, `dl/evaluation/` |
| `05_xai.ipynb` | Reconstruction-error maps, Seg-Grad-CAM, Integrated Gradients and faithfulness | planned | `dl/evaluation/xai.py` |

The template is preserved at its current path. Its markdown explanations,
ownership map, contract assertions and section exercises stay. Its inline
authoritative stubs move into `dl/`; until that migration lands, its banner
marks them non-authoritative. The feature contract is
[`specs/002-notebook-workflow/spec.md`](../../specs/002-notebook-workflow/spec.md).

## Official path versus learning path

| | Official | Learning |
|---|---|---|
| Entry point | `make train`, `make eval`, `make export`, XAI entry point | A notebook cell |
| Config | `profile: official`; pinned normal-road manifest, scene-grouped split hash, seed and config hash | `profile: learning`; reproducible but not official evidence |
| Record | `docs/experiments/NNNN-*.md` | `docs/experiments/learning/NNNN-*.md` |
| Can be cited in README/report | Yes, after review | **No** |
| Can select, tune or promote | Yes, under ADR-0008 and normal-road validation | **No** |
| Promotion path | Official record and registry decision | Rerun under an official config; never copy the notebook number |

A learning record is still a record: it names the commit, config, command, seed
and environment, so the exercise can be repeated. It is simply not evidence for
a published number. See [`docs/experiments/README.md`](../../docs/experiments/README.md).

## What a notebook may contain

- Explanations, Feynman checks, pitfalls and short exercises.
- Calls into `dl/` with `inspect.getsource` or equivalent source walkthroughs.
- Intermediate tensors, score maps, masks, curves and error panels produced by
  the shared implementation.
- A controlled learning run with a `profile: learning` config and a learning
  record.
- A short **concept check** on toy data, clearly marked as illustrative only.

## What it may not contain

- An authoritative model, training loop, loss, metric, threshold selector,
  post-processor, export path or XAI method.
- A direct write to `docs/experiments/`, `README.md` or the report.
- Training, fine-tuning, early stopping, model selection or threshold tuning on
  the 60 RoadAnomaly frames.
- An import or `%run` of another notebook.
- A new runtime container, deployment component or C4 relationship.
- A hidden copy of a metric under another name. F1 and Dice are one binary-mask
  metric, not two notebook results.

## Concept-check contract

A concept check is a teaching device, not a miniature official implementation.

- Tag the cell `concept-check` in notebook metadata.
- Prefix definitions and persistent variables with `toy_` (`toy_softmax`, `toy_msp`,
  `toy_iou`).
- Caption it: "Illustrative only; not used for reported results."
- Use toy arrays or scores. Do not load benchmark frames, normal-road data or a
  checkpoint.
- Write no file and no experiment record.
- Do not use a `toy_` variable in a later non-concept cell.
- Do not shadow an official function name, even inside the tagged cell.

`plot_*`, `show_*` and `display_*` helpers are presentation, not authoritative
logic, and are allowed outside concept-check cells as long as they do not compute
an official metric or change a score map.

## Prerequisites and honesty

- The normal-road manifest, class map and scene-grouped split hash are not pinned
  yet (gap G10). A notebook that reaches training must stop with an actionable
  message; it must not invent data, paths or results.
- `data/` is evaluation-only. `01_dataset_eda` may inspect it; no notebook may
  train on it or tune on it.
- A full training run needs explicit approval and a pinned manifest. Reading,
  inspecting and small CPU exercises do not.
- Strip outputs before committing. Keep paths repository-relative and keep
  secrets and machine-specific paths out of the notebook.
- Adding a notebook does not change a requirement's status. That decision stays
  with [`docs/validation/requirements-matrix.md`](../../docs/validation/requirements-matrix.md).

## Links

- Package contract: [`dl/README.md`](../README.md)
- Run profiles and config rules: [`configs/README.md`](../../configs/README.md)
- Metric contract: [`docs/metrics.md`](../../docs/metrics.md)
- XAI contract: [`docs/xai.md`](../../docs/xai.md)
- Dataset facts and evaluation-only protocol: [`docs/dataset.md`](../../docs/dataset.md)
- Experiment records: [`docs/experiments/README.md`](../../docs/experiments/README.md)
- Feature spec: [`specs/002-notebook-workflow/spec.md`](../../specs/002-notebook-workflow/spec.md)
