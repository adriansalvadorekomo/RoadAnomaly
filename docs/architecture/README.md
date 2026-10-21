# Architecture

[`workspace.dsl`](workspace.dsl) is the single source of truth for the C4 model.
The committed PNGs are rendered from that file; there is no second architecture
JSON, hand-edited diagram or generated HTML. The model is target-state: the
dataset and contract tests exist, while models, metrics, XAI, serving and
deployment are planned.

Status vocabulary and the evidence bar are defined in
[`docs/validation/requirements-matrix.md`](../validation/requirements-matrix.md).

## C1 — system context

![C1 system context](diagrams/c1-system-context.png)

The context view shows the two human roles and three external dependencies.
`RoadAnomaly` is the repository and planned offline pipeline; the normal-road
corpora and pretrained weights are external inputs, not assets tracked here.
GitHub Actions is the only external system that is implemented today.

## C2 — offline pipeline

![C2 offline pipeline](diagrams/c2-offline-pipeline.png)

This view is the planned CRISP-DM data and evaluation path, not a running
system. The implemented containers are the 60-frame benchmark, the contract
tests and the experiment-record template. Everything else is a target:

| Container | Purpose | Status |
|---|---|---|
| RoadAnomaly benchmark | 60 tracked frames, masks and credits; evaluation-only | `implemented` |
| Contract tests | Dataset integrity plus architecture/documentation guardrails | `implemented` |
| Experiment records | Template and index; no run has been recorded | template only |
| Normal-road manifest | Pinned release, class map, label hashes and split hash | `missing` |
| Data pipeline | Decode, augment and scene-grouped `tf.data` batches | `missing` |
| Training | Autoencoder, U-Net and DeepLabV3+ on normal-road data | `missing` |
| Model artifacts | Checkpoints, SavedModels and preprocessing manifests | `missing` |
| Normal-road validation | Scene-grouped validation and native diagnostics | `missing` |
| Selection scorecard | Documented multi-criteria choice; no benchmark number | `missing` |
| RoadAnomaly evaluation | Common binary-mask metrics on all 60 held-out frames | `missing` |
| XAI evidence | Error maps, Seg-Grad-CAM, Integrated Gradients and faithfulness checks | `missing` |
| Model registry | All three candidates plus the `selected` alias | `missing` |

Online inference and deployment views are intentionally absent. No API, frontend,
Dockerfile, Kubernetes manifest, Argo CD application or Vercel project exists;
diagramming them now would imply a system that is not there.

## Guardrails encoded in the model

- **Evaluation-only benchmark.** The benchmark flows to evaluation, never to
  training, selection or the registry. There is no path from
  `benchmarkEvaluation` or `xai` to `registry`.
- **Selection is normal-road.** `normalRoadValidation` writes
  `selectionScorecard`; the scorecard chooses the alias and keeps all three
  candidates in the registry. No RoadAnomaly number appears in the scorecard or
  `selected.json`.
- **XAI is evidence, not promotion.** XAI consumes the selected model and writes
  to the experiment record. It has no edge to the registry.
- **Artifacts are immutable.** The registry is a release boundary; deployment
  would mount a digest-pinned bundle read-only. The delivery target is described
  in [ADR-0004](../adr/0004-vercel-and-gitops-deployment.md); no delivery
  container is modelled yet.

See [ADR-0001](../adr/0001-evaluation-only-benchmark.md),
[ADR-0008](../adr/0008-promotion-and-model-registry.md),
[ADR-0010](../adr/0010-model-lineup-and-evaluation-contract.md) and
[ADR-0012](../adr/0012-structurizr-c4-architecture.md).

## CRISP-DM mapping

C4 models structure, not process. The six CRISP-DM phases are mapped here as a
table instead of a second diagram; the methodology is recorded in
[ADR-0007](../adr/0007-crisp-dm-methodology.md).

| Phase | What it owns | Where it appears | Status |
|---|---|---|---|
| 1. Business understanding | Scope, three-model comparison, evaluation-only protocol, success criteria | C1; README §1; ADR-0001/0010 | `in progress` |
| 2. Data understanding | RoadAnomaly facts and EDA; normal-road release, licence and scene audit | Benchmark container; dataset tests | `in progress` — EDA and normal-road manifest missing |
| 3. Data preparation | Pinned manifest, class map, label hashes, scene-grouped splits, `tf.data` pipeline | Normal-road manifest and data pipeline | `missing` |
| 4. Modeling | Autoencoder, U-Net, DeepLabV3+ training and exported artifacts | Training and model artifacts | `missing` |
| 5. Evaluation | Metric harness, normal-road selection, held-out RoadAnomaly scoring, XAI and faithfulness | Validation, scorecard, benchmark evaluation, XAI | `missing` — contracts only |
| 6. Deployment | Registry, FastAPI, Streamlit, Astro, containers and GitOps | Registry only in C2; online views deferred | `missing` |

## Render and validate

The renderer is pinned to Structurizr CLI `v2025.11.09` and a headless Chromium.
Structurizr CLI itself does not export PNG; the official workflow is a static
site rendered in a browser. `render.sh` automates that workflow:

```bash
# From the repository root. Requires Java 21, Chromium and Pillow.
./docs/architecture/render.sh

# Semantic contract and committed-asset check.
.venv/bin/pytest -q tests/architecture -v
```

On first use the script downloads the pinned CLI to
`~/.cache/roadanomaly/structurizr-cli-v2025.11.09/`; set `STRUCTURIZR_CLI` to an
existing `structurizr.sh` to use a local copy. It exports the static site,
hides the viewer chrome, captures both views at 2× and crops the whitespace.
`diagrams/manifest.json` records the DSL SHA-256, renderer and each PNG's
dimensions, so the tests fail when the source changes without a re-render. CI
validates the DSL and runs the contract tests; it does not need a browser.

## Planned API and frontend boundary

No service exists, so this is a contract to implement, not an architecture view.
`POST /predict` accepts `multipart/form-data` with `file`, `model` (one of
`autoencoder`, `unet`, `deeplabv3plus`) and an optional `threshold`. It returns
the model ID, immutable digest, echoed threshold, input dimensions, base64 PNG
score map/mask/overlay, pixel statistics and timing.

These are **pixel statistics, not evaluation metrics**: an upload has no ground
truth, so the API must not compute IoU, Dice, AUROC or AUPRO. The Streamlit
prototype may re-threshold a cached score map but must display the threshold
used. The Astro landing page makes no runtime API call. See
[ADR-0006](../adr/0006-astro-and-streamlit-frontend.md) and
[`backend/README.md`](../../backend/README.md).

## Artifact lineage

```
normal-road validation -> selection scorecard -> selected alias
        |                         |
        +-> all three candidate SavedModels + manifests (audit trail)

RoadAnomaly evaluation -> experiment record -> report (report-only)
XAI evidence -----------> experiment record -> prototype (only when present)
```

The registry keeps all three candidates; `selected.json` is an alias, not the
only artifact. A model manifest records the git SHA, config hash, normal-road
manifest ID and split hash, seed, framework versions, input signature, default
threshold, native validation metrics and artifact digest. RoadAnomaly numbers
never enter the manifest or the selection scorecard.
