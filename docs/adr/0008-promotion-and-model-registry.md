# 0008. Promotion, model registry and artifact lineage

- **Status:** Accepted (target state; implementation not started)
- **Date:** 2026-10-19
- **Deciders:** whole team

## Context

The first architecture draft put the shared evaluation harness between the
models and the registry. That drawing was ambiguous: it could be read as
"RoadAnomaly metrics promote a model", which is the exact leakage
[ADR-0001](0001-evaluation-only-benchmark.md) exists to prevent. It also left
two operational questions unanswered:

- Does the registry hold all three models or only the selected one?
- How does a SavedModel reach the API in Minikube without being baked into the
  image or copied into Git?

The absence of an export/registration step made every downstream serving claim
untraceable.

## Decision

### Selection and promotion

1. **Selection uses normal-road validation only.** The comparison and the
   selected alias are decided from scene-grouped folds drawn from the
   normal-road corpus. The candidate with the chosen operating threshold is
   recorded in the registry manifest.
2. **RoadAnomaly is a held-out scoring set, never a promotion signal.** Its 60
   frames may not influence weights, early stopping, thresholds, model
   selection, the selected alias or a deployment gate. Its metrics are reported
   as zero-shot and, separately, threshold-tuned, exactly as ADR-0001 requires.
3. **XAI does not promote either.** Explanations are evaluation evidence for the
   selected model; they are not a ranking signal. See
   [ADR-0009](0009-xai-evaluation-gate.md).

### Registry contents

The registry keeps **all three candidate SavedModels**, not just the winner:

```
registry/<release>/
├── A/                 SavedModel + manifest.json
├── B/                 SavedModel + manifest.json
├── C/                 SavedModel + manifest.json
└── selected.json      alias + digest + normal-road selection evidence
```

Each `manifest.json` records at least:

- git commit and config path/hash;
- random seed and TensorFlow/Python versions;
- normal-road dataset manifest ID and split hash;
- input signature, preprocessing version and default threshold;
- normal-road validation metrics used for selection;
- artifact digest and creation command.

RoadAnomaly metrics do **not** appear in the selection fields. They are written
to `docs/experiments/` and may be copied into a report or the static landing
page, but they are not an input to `selected.json`.

### Artifact supply chain

- Export runs in `dl/inference/` and produces a SavedModel with a serving
  signature plus the manifest. Nothing is trained at serve time.
- A release bundle containing the three candidate models, manifests and
  `selected.json` is published as an **OCI artifact** to GHCR alongside the API
  and prototype images. Weights are never committed to Git and never baked into
  an application image.
- The API loads the bundle from a read-only mount. Compose uses the local
  `artifacts/` directory for development; Minikube uses an init container or a
  pre-seeded read-only volume populated from the GHCR artifact.
- Image and model references are promoted by **immutable digest**. Release
  tags such as `v1.0.0` and `sha-<commit>` are allowed; `latest` and moving
  `major.minor` tags are not used for deployment.

### Delivery

- CI runs the quality gate. CD runs after it and publishes only gated,
  immutable references.
- Promotion is a commit to the Kubernetes overlay (pinned image digests and
  model bundle digest), not a `kubectl apply` from CI.
- Argo CD pulls the desired state from Git and syncs Minikube. CI has no
  cluster credentials and does not push workloads into the cluster.
- Vercel builds the Astro landing page from its Git integration; the static
  page reads only committed experiment records.

## Alternatives considered

| Option | Why not |
|---|---|
| Promote the model with the best RoadAnomaly score | Direct leakage: the benchmark becomes a selection set and the reported number is no longer held out |
| Store only the selected model | Loses the audit trail and makes the comparison unreproducible |
| Bake the SavedModel into the API image | Couples model releases to image releases, makes rollback coarse and usually bloats the image |
| Copy weights into Git or a Kubernetes manifest | Binary artifacts do not belong in Git; manifests cannot carry a reproducible model bundle |
| Use `latest` or `v1.2`-style moving tags | A redeploy can silently change the model or code under the same name |
| Let CI run `kubectl apply` with cluster credentials | Bypasses Git as the source of truth and leaves no reviewable promotion commit |

## Consequences

**What gets easier.** A reviewer can trace a served prediction to a model digest,
a manifest and a selection record. Rolling back means reverting one promotion
commit. The benchmark stays report-only by construction, not by convention.

**What gets harder.** Every candidate must be exported and manifested, not just
the winner. The API needs a read-only artifact mount and a startup failure mode
when the bundle is missing. CI and CD need a promotion step that is separate
from image publication.

**How we would know this was wrong.** If the module cannot run a multi-model
registry, or if the selected model cannot be served from a read-only artifact
without a network dependency at request time, this decision should be revisited.
