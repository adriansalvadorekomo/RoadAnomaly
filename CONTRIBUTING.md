# Contributing

Six people, three weeks, one deadline. This file exists so nobody has to ask
"how do we do this here?" twice.

## One-time setup

```bash
git clone https://github.com/adriansalvadorekomo/RoadAnomaly.git
cd RoadAnomaly
make install                 # .venv + dev, ML and API dependencies
make data-check              # confirms the dataset is intact
nbstripout --install         # strips notebook outputs on commit
```

`make lint type test` must pass before you push. It is the same thing CI runs.

## Branching

Short-lived branches off `main`, merged by pull request. Nothing is committed
directly to `main`.

```
feat/ae-baseline        new capability
fix/mask-decode-edge    a bug
exp/resynth-threshold   an experiment that might not work out
docs/adr-0004           documentation
```

`exp/*` branches are expected to be abandoned sometimes. Say so in the issue
and delete the branch — a negative result written into `docs/experiments/` is a
contribution, and an abandoned branch is not a failure.

## The five rules

1. **`main` stays green.** If your change breaks CI, fixing it is the next
   thing you do — not the thing you do after lunch.
2. **Never fit weights on the 60 evaluation frames.** See
   [ADR-0001](docs/adr/0001-evaluation-only-benchmark.md). This is not a style
   preference; a model trained on the evaluation set produces numbers that mean
   nothing and would have to be withdrawn.
3. **Metrics are defined once, in `ml/evaluation/metrics.py`.** If your model
   needs a new one, add it there so all three models get it.
4. **A reported number needs an experiment file.** Anything in the README or the
   report must trace to `docs/experiments/NNNN-*.md` with the commit, config and
   command. The PR template asks about this.
5. **No silent suppressions.** A `# type: ignore`, `@ts-ignore`, skipped test or
   lowered threshold needs a comment on the line above saying why. If the reason
   is "it was failing", the fix is not a suppression.

## Definition of done

- [ ] `make lint type test` passes locally
- [ ] New behaviour has a test, or the PR says why it cannot have one
- [ ] Docstrings on anything another person will import
- [ ] If it changes what the report claims, `docs/experiments/` is updated
- [ ] One reviewer from the affected workstream (CODEOWNERS does this for you)
- [ ] No secrets, no `data/credits.txt` edits, no committed artefacts

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
