## What changed

<!-- One or two sentences. Link the issue if there is one: Closes #12.
     Feature work: link the spec, e.g. specs/001-normal-road-manifest/. -->

**Spec:** `specs/NNN-name/` or `N/A` (docs/chore)

## Type of change

- [ ] Bug fix
- [ ] New model or training feature
- [ ] Evaluation / metrics
- [ ] Backend or frontend
- [ ] Infrastructure, CI/CD or Docker
- [ ] Documentation or report
- [ ] Dataset tooling

## Does this change any reported number?

- [ ] **No** — this change cannot affect a metric in `docs/experiments/`
- [ ] **Yes, normal-road selection** — I re-ran the affected experiment and
      updated `docs/experiments/`, the selection record and `README.md`
- [ ] **Yes, RoadAnomaly held-out** — I re-ran the affected experiment and kept
      it in the report-only columns; selection and held-out scores are still
      separate

> A metric that changes without a re-run is the single easiest way to
> poison this project. If you are not sure, answer yes and re-run. Never move a
> RoadAnomaly number into the selection column to make a model look better.

## Verification

<!-- What did you actually run, and what did you see? Paste the command
     and the result. "Should work" is not verification. -->

```
$ make test
```

## Checklist

- [ ] `make lint` and `make type` pass locally
- [ ] `make test` passes locally (dataset + architecture contracts today)
- [ ] Feature work links a spec in `specs/`; docs/chores say `N/A`
- [ ] Dataset assumptions still hold (`make data-check`) if I touched `data/` or `dl/data/`
- [ ] The normal-road dataset manifest and split hash are pinned if this is a training run
- [ ] No notebook outputs committed by accident (`nbstripout` applied)
- [ ] If I added an architecture decision, it is recorded in `docs/adr/`
- [ ] The architecture contract tests pass if I touched `docs/architecture/`
- [ ] I did not add a `@ts-ignore`, `# type: ignore`, or a skipped test
      without explaining why on the line above it
- [ ] No weights, model bundles or secrets are committed; no `latest` deployment tag

## Screenshots or outputs

<!-- Only for UI or qualitative model results. Input | ground truth | prediction. -->
