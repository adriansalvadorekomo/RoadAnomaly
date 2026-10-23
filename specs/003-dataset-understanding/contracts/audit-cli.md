# Contract: audit CLI

**Feature**: `003-dataset-understanding` · **Version**: 1.0 · **Scope**: MVP

## Command

```bash
python -m dl.data.audit [--check] [--data-root PATH] [--output-root PATH]
```

`make data-audit` invokes generate mode with repository defaults. `make data-audit-check`
invokes `--check`. The command is offline, CPU-only, TensorFlow-free and Matplotlib-free.

Defaults, relative to the repository root:

| Option | Default |
|---|---|
| `--data-root` | `data` |
| `--output-root` | `docs/validation` |

Absolute paths are accepted for tests and diagnosis. Canonical output must not contain a home
directory or machine-specific path. Frame and label paths in the JSON are logical data-relative
paths, so temporary data roots do not leak into evidence.

## Generate mode

The command computes one complete `AuditResult`, validates the serialized JSON, renders the
Markdown report from the validated JSON bytes, and publishes exactly two canonical files:

```text
<output-root>/roadanomaly-eda.json
<output-root>/roadanomaly-eda.md
```

There is no artifact root, overlay, figure, review ledger, readiness report, output manifest or
`.audit-staging/` directory in the MVP.

### Output directory rules

- `--output-root` must already exist and be a directory; the CLI does not create directories.
- Inside the repository, only `docs/validation` is an allowed output root. A run with any other
  in-repository output root exits `4`.
- Outside the repository, a temporary output root is allowed; it receives only the two filenames.
- No subdirectory, split, class map, manifest, figure, overlay or ledger may be created.
- Temporary siblings are exactly `roadanomaly-eda.json.tmp` and `roadanomaly-eda.md.tmp` in the
  output root. They are removed on a normal failure.
- The output root is resolved with symlink/traversal checks. A symlink escape or a path escaping
  the configured root exits `4`.

### Generate sequence

1. Read `data/` and compute all evidence. A fingerprint mismatch, corrupt/missing input,
   invalid label or instance/semantic mismatch exits `2` before any file is created.
2. Serialize the complete result deterministically to memory and validate it against
   `contracts/audit-summary.schema.json` with `jsonschema.Draft202012Validator`. Failure exits `3`.
3. Render the Markdown report from the validated JSON bytes and the JSON SHA-256. Failure exits
   `3`.
4. Write both documents to the two temporary siblings and `fsync` them.
5. Replace `roadanomaly-eda.json` and then `roadanomaly-eda.md` with `os.replace`.
6. Remove any remaining temporary sibling and return `0`.

The report contains the validated JSON SHA-256. The JSON does not contain the report hash. This
one-way orientation avoids a circular digest and makes the JSON the authoritative source.

### Failure and crash behavior

A normal failure before step 5 removes temporary files and leaves the previous canonical pair
unchanged. The two replacements are individually atomic, not set-atomic. If a process crashes or
the second replacement fails between the two replacements, the JSON may be new while the report
is old (or vice versa); exit `3` for a replacement failure. The JSON remains authoritative;
`--check` re-renders the report and compares its source digest, so a mixed pair is detected. The
MVP does not add a journal, backup, rollback transaction or claim that a crash can never expose a
mixed pair. This is a documented limitation, not a success guarantee.

### Determinism

- JSON: UTF-8, sorted keys, LF, one trailing newline, no timestamp.
- Markdown: UTF-8, LF, deterministic section and row order, no timestamp or host path.
- The only volatile field is `environment.commit`; check mode pins it to the committed value.
- Repeated runs on the same checkout, environment and commit produce byte-identical JSON and
  report.

## Check mode

`--check` writes nothing, creates no temporary files and does not require a normal-road corpus,
TensorFlow, a GPU, network access, overlays, figures or a ledger. It verifies:

1. both committed files exist and are readable;
2. the committed JSON parses and validates against the Draft 2020-12 schema;
3. the published JSON's `environment.command` is exactly `make data-audit`;
4. the recomputed result matches the committed JSON after pinning `environment.commit` to the
   committed value (all other fields must match);
5. recomputed fingerprint and counts are consistent with the historical constant;
6. the report is byte-identical to a fresh render from the validated committed JSON and its
   recorded source JSON SHA-256;
7. the report contains all ten required sections and no report-hash field.

A committed-output mismatch exits `1`. A fingerprint or data failure exits `2`. A schema,
rendering, parsing or I/O failure exits `3`. A policy violation exits `4`. Check mode never
rewrites or repairs committed evidence.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Generate succeeded, or check found the committed pair consistent |
| `1` | Committed output mismatch in check mode |
| `2` | Data failure: fingerprint drift, missing/corrupt input, invalid mask, or instance/semantic mismatch |
| `3` | Input, schema, rendering, serialization or I/O failure before publication |
| `4` | Output-policy violation: wrong root, subdirectory, symlink escape or extra filename |

On every non-zero exit, print an actionable path or invariant. A fingerprint mismatch prints the
historical and computed hashes and both historical and current counts. An instance/semantic
mismatch prints each affected frame with its extra and missing pixel counts. The command never
skips, repairs, renumbers, clips or normalizes an input.

## Environment and dependencies

The CLI reads only local files and installed package versions. It does not read secret
environment variables, invoke a shell or use the network. The JSON records the source commit,
canonical command, Python, NumPy, Pillow and `jsonschema` versions, audit version, historical
fingerprint/counts and current counts. `jsonschema` is a mandatory runtime dependency declared in
`requirements/dev.txt`; if unavailable or validation fails, generation exits `3` and publishes
nothing.

## Out-of-scope guarantees

The CLI creates no dataset manifest, class map, split, split hash, experiment record, model,
metric, overlay, figure, review ledger, readiness report or source recommendation. It does not
modify `data/`, the requirements matrix, protected documentation or any ADR.
