# Contributing

Six people, three weeks, one deadline. This file exists so nobody has to ask
"how do we do this here?" twice. Coding agents also follow
[`AGENTS.md`](AGENTS.md), which is the short, strict version of this file.

## One-time setup

```bash
git clone https://github.com/adriansalvadorekomo/RoadAnomaly.git
cd RoadAnomaly
make install                 # .venv + dev, deep learning, API and prototype dependencies
make data-check              # confirms the dataset is intact
pytest -q tests/architecture # confirms the promotion rule and diagram assets
nbstripout --install         # strips notebook outputs on commit
```

`make lint type test` must pass before you push. It is the same thing CI runs,
including the architecture contract tests.

## Branching

Short-lived branches off `main`, merged by pull request. Nothing is committed
directly to `main`.

```
feat/ae-baseline        new capability
fix/mask-decode-edge    a bug
exp/resynth-threshold   an experiment that might not work out
refactor/repo-structure structural change, no behaviour change
docs/adr-0004           documentation
```

`exp/*` branches are expected to be abandoned sometimes. Say so in the issue
and delete the branch — a negative result written into `docs/experiments/` is a
contribution, and an abandoned branch is not a failure.

## Spec-driven development

Non-trivial feature work starts with a spec in `specs/NNN-kebab-name/`:

```text
/speckit.specify  →  /speckit.plan  →  /speckit.tasks  →  /speckit.implement
```

Link the ADR, metric contract or issue the feature depends on from `spec.md`.
Do not create a spec for a typo, a chore or a documentation-only change. A spec
and its checked tasks are plans, not evidence: the
[requirements matrix](docs/validation/requirements-matrix.md) still decides
status, and `docs/experiments/` still decides published numbers. See
[ADR-0013](docs/adr/0013-spec-driven-development.md) and
[`docs/sdd.md`](docs/sdd.md).

## The six rules

1. **`main` stays green.** If your change breaks CI, fixing it is the next
   thing you do — not the thing you do after lunch.
2. **Never fit weights or select a model on the 60 evaluation frames.** See
   [ADR-0001](docs/adr/0001-evaluation-only-benchmark.md). The separately
   reported threshold-tuned regime may choose one scalar on scene-grouped
   benchmark folds; it never promotes a model. Early stopping and model
   selection use the normal-road validation split. This is not a style
   preference; a model trained or selected on the evaluation set produces
   numbers that mean nothing and would have to be withdrawn.
3. **Metrics are defined once, in `dl/evaluation/metrics.py`.** If your model
   needs a new one, add it there so all three models get it.
4. **A reported number needs an experiment file.** Anything in the README or the
   report must trace to `docs/experiments/NNNN-*.md` with the commit, config,
   command, normal-road manifest and split hash. Normal-road selection metrics
   and RoadAnomaly held-out scores go in separate rows. The PR template asks
   about this.
5. **No silent suppressions.** A `# type: ignore`, `@ts-ignore`, skipped test or
   lowered threshold needs a comment on the line above saying why. If the reason
   is "it was failing", the fix is not a suppression.
6. **Status words are evidence claims.** `implemented` means a file or command
   proves it; `in progress`, `missing` and `blocked` are defined in
   [`docs/validation/requirements-matrix.md`](docs/validation/requirements-matrix.md).
   A README sentence is not evidence, and neither is a directory that contains
   only `.gitkeep`.

## Delivery and model-artifact rules

- **Selection comes from normal-road validation.** The registry keeps all three
  candidate SavedModels and manifests; `selected.json` is an alias. There is no
  RoadAnomaly-to-registry path ([ADR-0008](docs/adr/0008-promotion-and-model-registry.md)).
- **XAI is a gate, not a promotion signal.** The methods are fixed in
  [ADR-0011](docs/adr/0011-xai-methods-and-faithfulness.md). Do not substitute a
  method, and do not render a placeholder explanation
  ([ADR-0009](docs/adr/0009-xai-evaluation-gate.md),
  [`docs/xai.md`](docs/xai.md)).
- **No weights in Git or images.** Build a versioned model bundle, publish it to
  GHCR, and mount it read-only. Compose uses a local `artifacts/` mount.
- **Deploy immutable references.** Pin images and model bundles by digest; no
  `latest`, no moving `major.minor` tags. Promotion is a reviewed commit, and
  Argo CD pulls it. CI does not hold cluster credentials.

## Definition of done

- [ ] `make lint type test` passes locally
- [ ] New behaviour has a test, or the PR says why it cannot have one
- [ ] Docstrings on anything another person will import
- [ ] If it changes what the report claims, `docs/experiments/` is updated
- [ ] If it changes a capability, `docs/validation/requirements-matrix.md` is updated
- [ ] If it changes the diagram, `pytest -q tests/architecture` passes and the PNGs are regenerated
- [ ] Normal-road selection and RoadAnomaly held-out results remain separate
- [ ] One reviewer from the affected workstream (CODEOWNERS does this for you)
- [ ] No secrets, no `data/credits.txt` edits, no committed artefacts or weights

## Commits

Conventional prefixes keep the log skimmable:

```
feat: autoencoder reconstruction-error scoring
fix: handle semantic-only frames in the loader
exp: threshold sweep on scene-grouped folds
docs: ADR-0003 on the serving stack
ci: gate container build on Dockerfile presence
chore: bump ruff
```

Write the subject in the imperative, keep it under ~70 characters, and put the
*why* in the body when it is not obvious. The diff already says what changed.

## Reviewing

Review the claim, not the formatting — `ruff` handles formatting. Ask:

- Is the number reproducible from what is written down?
- Is a failure being hidden (a mean without a distribution, a dropped frame,
  a cherry-picked example)?
- Does this make `main` harder to keep green?

Disagreement about a decision that is expensive to reverse becomes an
[ADR](docs/adr/), not a long comment thread.
