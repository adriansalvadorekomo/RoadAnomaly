# Quickstart: RoadAnomaly dataset audit MVP

**Feature Directory**: `003-dataset-understanding` · **Branch**: `docs/adopt-sdd` · **Date**: 2026-10-22

This guide validates the future MVP implementation described in [plan.md](./plan.md). It does not
claim the implementation exists yet. Run commands from the repository root.

## Prerequisites

- Python 3.12 and the project virtual environment.
- The tracked `data/` checkout: 60 frames, 677 files, 13,135,474 bytes.
- `make install`, which supplies NumPy, Pillow and `jsonschema`. Matplotlib may be present from an
  unrelated pre-existing requirements change, but the MVP does not import or require it.
- No TensorFlow, GPU, network or normal-road corpus is required.

```bash
make venv
make install
make data-check
```

## 1. Generate the evidence

Do not run this before T025 passes. The first canonical run is T026, after the complete result and
report tests pass.

```bash
make data-audit
```

Expected outputs, exactly two canonical files:

| Path | Expected |
|---|---|
| `docs/validation/roadanomaly-eda.json` | Complete schema-valid summary with 16 root fields |
| `docs/validation/roadanomaly-eda.md` | Report rendered from the validated JSON, with 10 sections and the JSON SHA-256 |

No `.audit-staging/`, artifact root, overlay, figure, ledger, readiness report or output manifest
is created.

The JSON/report must show:

- fingerprint match `7c16…f4e2`; historical 677 files and 13,135,474 bytes; current counts
  separately;
- 60 frames, 60 label directories, 46 instance-annotated, 14 semantic-only;
- 46/46 exact instance/semantic equality, 0 extra pixels, 0 missing pixels, 14 excluded;
- pooled coverage `9.849561 %`, range `0.374674–42.328559 %`, median `6.622938 %`, six frames
  below 1 %;
- category counts `31/15/8/3/3`, labelled object categories, not scenes;
- object scale `35/20/46`, medians `86.7/85.0/107.0/51.2`, denominator 201;
- order mapping 35/46 agree, 11/46 disagree, complete affected lists;
- ROI 11/201 out-of-bounds, 17/201 non-tight, 201/201 centroids inside, complete lists;
- duplicate methods exact/decoded/dHash, no pairs and the method limitation;
- 60 credit entries, 24 missing licence tokens, four source groups covering 13 frames, one
  four-frame group without a URL;
- annotation `CC BY-SA 4.0`, code `MIT`, `legal_conclusion: not_made`;
- ADR-0010 threshold contradiction as an open unresolved item; P0-1 through P0-4 and G10 open;
- no visual-registration, figure or readiness claim.

The report is a renderer over validated JSON. It must not recompute a number or load an image.

## 2. Check without writing

```bash
make data-audit-check
```

Expected: exit `0`; no file changes, no temporary files. Check mode validates the committed JSON
against the Draft 2020-12 schema, pins `environment.commit`, recomputes the result, compares all
other fields, re-renders the report from the committed JSON, and verifies the report's source JSON
SHA-256 and bytes. It requires `environment.command == "make data-audit"`.

If check exits non-zero:

| Exit | Meaning |
|---|---|
| `1` | Committed JSON/report mismatch, including a mixed pair; inspect and regenerate after review |
| `2` | Fingerprint/data drift, corrupt input, invalid mask or instance/semantic mismatch; do not replace the baseline or edit masks |
| `3` | Input/schema/rendering/I/O failure; fix the source, never skip or invent |
| `4` | Output-policy violation; stop and inspect the attempted path |

## 3. Prove determinism

Run generation twice and compare the two committed files:

```bash
make data-audit
sha256sum docs/validation/roadanomaly-eda.json \
  docs/validation/roadanomaly-eda.md > /tmp/opencode/audit-first.sha256
make data-audit
sha256sum docs/validation/roadanomaly-eda.json \
  docs/validation/roadanomaly-eda.md > /tmp/opencode/audit-second.sha256
diff -u /tmp/opencode/audit-first.sha256 /tmp/opencode/audit-second.sha256
```

Expected: no diff. The only volatile field is `environment.commit`; the same checkout and commit
must produce byte-identical JSON and report.

## 4. Drift simulation on a temporary copy

Do **not** modify `data/`. Copy it outside the repository and run against the copy:

```bash
mkdir -p /tmp/opencode/audit-drift/output
cp -a data /tmp/opencode/audit-drift/data
printf 'temporary drift\n' >> /tmp/opencode/audit-drift/data/readme.md
python -m dl.data.audit \
  --data-root /tmp/opencode/audit-drift/data \
  --output-root /tmp/opencode/audit-drift/output
```

Expected: exit `2`; stderr prints the historical and computed hashes plus historical and current
counts; no JSON or report is written. The historical constant is not replaced. Delete the
temporary copy after inspection.

## 5. Quality gate

```bash
make lint type test
make test-fast
make data-check
python - <<'PY'
import json
from pathlib import Path
import jsonschema
schema = json.loads(Path('specs/003-dataset-understanding/contracts/audit-summary.schema.json').read_text())
jsonschema.Draft202012Validator.check_schema(schema)
print('schema meta-validation: ok')
PY
git status --short
git diff -- data docs/experiments docs/metrics.md docs/dataset.md .specify/memory/constitution.md docs/adr
```

Expected: lint, format, mypy, tests and the dataset contract pass; schema meta-validation prints
`ok`; no `data/`, experiment, metric, dataset, constitution or ADR change; no split, class map or
manifest; no canonical output from a component checkpoint.

## 6. Extensions (not validated here)

- Visual overlays and review ledger: `contracts/visual-review-ledger.md`.
- Aggregate figures: future rendering from the validated JSON.
- Normal-road readiness: `contracts/normal-road-readiness.md`.

These are post-MVP. The MVP must not claim visual registration, readiness or figure evidence.

## Failure and stop conditions

Stop and report rather than inventing data, paths or results if:

- the historical fingerprint does not match;
- a frame, label, mask or credit entry is missing;
- a frame is corrupt, or a mask has an unexpected value, size or colour mapping;
- the instance/semantic invariant fails (exit `2`, affected frame and extra/missing counts, no
  output);
- the schema, output-policy or report parity check fails;
- a normal-road source is absent (expected; do not acquire one);
- the requirements matrix would need an `implemented` status before evidence exists.

A missing prerequisite is a finding, not permission to create a fallback dataset, split, class map,
manifest or placeholder report.
