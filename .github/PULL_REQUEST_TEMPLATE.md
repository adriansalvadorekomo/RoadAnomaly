## What changed

<!-- One or two sentences. Link the issue if there is one: Closes #12 -->

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
- [ ] **Yes** — I re-ran the affected experiment and updated
      `docs/experiments/` and the results table in `README.md`

> A metric that changes without a re-run is the single easiest way to
> poison this project. If you are not sure, answer yes and re-run.

## Verification

<!-- What did you actually run, and what did you see? Paste the command
     and the result. "Should work" is not verification. -->

```
$ make test
```

## Checklist

- [ ] `make lint` and `make type` pass locally
- [ ] `make test` passes locally
- [ ] Dataset assumptions still hold (`make data-check`) if I touched `dl/data/`
- [ ] No notebook outputs committed by accident (`nbstripout` applied)
- [ ] If I added an architecture decision, it is recorded in `docs/adr/`
- [ ] I did not add a `@ts-ignore`, `# type: ignore`, or a skipped test
      without explaining why on the line above it

## Screenshots or outputs

<!-- Only for UI or qualitative model results. Input | ground truth | prediction. -->
