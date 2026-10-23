# Implementation Plan: RoadAnomaly dataset audit MVP

**Branch**: `docs/adopt-sdd` | **Feature Directory**: `003-dataset-understanding` | **Date**: 2026-10-22
**Spec**: [spec.md](./spec.md)

## Summary

Build one deterministic, read-only audit in `dl/data/audit.py`. It turns the accepted Stage 2
baseline into one schema-validated JSON summary and one Markdown report rendered from that
validated JSON. The MVP computes inventory, fingerprint, image/annotation integrity,
instance/semantic consistency, coverage, categories, object scale, instance mapping, ROI,
duplicates, credits, licensing evidence, provenance, documented-claim comparisons and
limitations. It does not train, select, tune, score, acquire data, create splits, invent a class
map or create a dataset manifest.

The core delivery is deliberately small:

- `docs/validation/roadanomaly-eda.json` is the authoritative evidence;
- `docs/validation/roadanomaly-eda.md` is a renderer over the validated JSON bytes;
- the report records the JSON SHA-256; the JSON does not contain the report hash;
- generation writes the two files through temporary siblings and per-file replacement;
- check mode validates the committed pair, recomputes the evidence, and writes nothing;
- fingerprint drift and annotation invariant failures are hard failures with no canonical output.

Visual overlays, advanced figures, the review ledger and the normal-road readiness gate are
post-MVP extensions. They are documented in the spec and their contracts, but they add no schema
fields, tasks, tests or acceptance blockers in this feature.

## Technical Context

**Language/Version**: Python 3.12

**Primary dependencies**: standard library (`argparse`, `csv`, `dataclasses`, `hashlib`, `json`,
`pathlib`, `re`), NumPy, Pillow, `jsonschema` for runtime Draft 2020-12 validation, and pytest.
No TensorFlow, GPU, network, Matplotlib or normal-road corpus is required. Matplotlib may remain
declared by an unrelated pre-existing requirements change, but the MVP must not import it.

**Storage**: Filesystem only. Reads `data/`, `data/credits.txt`, `data/readme.md`,
`docs/dataset.md` and `LICENSE`; writes only `roadanomaly-eda.json` and `roadanomaly-eda.md`
under the configured output root. No artifact root, staging directory, journal, database or
network resource.

**Testing**: `pytest` dataset tier and `tests/dataset/test_dataset_audit.py`, using `tmp_path`
data/output roots and the committed schema. Tests cover every computed family, the
instance/semantic invariant, fingerprint drift, corrupt inputs, schema validation, report
rendering from validated JSON, check mode, output policy, determinism and read-only guarantees.
Tests must run without TensorFlow, GPU, network, a normal-road corpus or a generated canonical
pair.

**Target Platform**: Linux/CI; offline, CPU-only.

**Project Type**: Single Python package plus CLI inside the existing monorepo.

**Performance Goals**: Full audit under about 60 seconds on a CI-class CPU; one frame at a time;
memory bounded by one frame and its masks.

**Constraints**: Read-only `data/`; deterministic JSON/report; no timestamp; `environment.commit`
is the only volatile field and check mode pins it; no split, class map or manifest creation; no
source survey or download; no model, metric, threshold or benchmark-use decision; no figures,
overlays, ledger or readiness output.

**Scale/Scope**: 60 frames, 60 label directories, 46 instance-annotated frames, 14 semantic-only
frames, 201 instances, historical 677 files / 13,135,474 bytes; current counts are reported
separately.

**Unknowns**: None for the MVP. P0-1 through P0-4, G10 and the ADR-0010 threshold contradiction
remain open scientific items and are reported, not resolved.

## Constitution Check

| Constitution gate | How this plan satisfies it | Status |
|---|---|---|
| 3 — Benchmark is evaluation-only | Descriptive audit only; no fitting, selection, tuning or promotion | PASS |
| 4 — Model lineup and label contract unchanged | No model code; no class map; P0-1 and label-contract questions remain open | PASS |
| 5 — Reproducibility | Fixed fingerprint recipe, deterministic JSON/report, committed evidence and check mode | PASS |
| 6 — Selection on normal-road validation only | Readiness is an extension; no source is selected, ranked or used | PASS |
| 7 — Single metric definition | Dataset descriptive statistics only; no model metric | PASS |
| 8 — Evidence | Outputs are validation evidence, not an experiment record | PASS |
| 9 — XAI is report-only | XAI is out of scope | PASS |
| 10 — Quality | Python 3.12, typed module, 100-column style, `make lint type test` | PASS |
| 11 — Tests | New dataset tests cover every computed family and failure path | PASS |
| 12 — Extensibility | Stable CLI, one JSON Schema, one report contract; extensions separate | PASS |
| 13 — Limits | No secrets, no data edits, no app/deployment work | PASS |
| ADR-0001 / ADR-0007 / ADR-0010 | Evidence remains CRISP-DM phase 2; ADR-0010 contradiction is reported open | PASS |

**Post-design check**: No additional violation. Complexity tracking is empty.

## Project Structure

```text
specs/003-dataset-understanding/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
└── contracts/
    ├── audit-cli.md
    ├── audit-summary.schema.json
    ├── eda-report.md
    ├── normal-road-readiness.md   # post-MVP extension
    └── visual-review-ledger.md    # post-MVP extension

dl/
├── __init__.py
└── data/
    ├── __init__.py
    └── audit.py                   # computation, CLI, JSON and report renderers

tests/
└── dataset/
    └── test_dataset_audit.py

docs/validation/
├── roadanomaly-eda.json            # canonical machine-readable evidence
└── roadanomaly-eda.md              # derived report
```

`Makefile` gains `data-audit` and `data-audit-check`. No notebook, backend, frontend, deployment
or artifact tree is changed. The existing `data/` tree is read-only.

**Structure decision**: A single module in the existing `dl/` package keeps computation, schema
serialization and report rendering from drifting. The JSON is small and the report is derived;
no second implementation is permitted.

## Design Decisions

1. **One authoritative schema.** `contracts/audit-summary.schema.json` is the only JSON Schema.
   It has 16 root fields. The report is generated only after the JSON validates.
2. **One-way digest.** The report includes the SHA-256 of the validated JSON bytes. The JSON has
   no report hash and no output-manifest object.
3. **Success-only drift record.** A fingerprint mismatch exits `2` with historical and current
   hashes/counts on stderr and writes no canonical output. The schema only represents a matched
   fingerprint; it never stores a misleading partial or drifted canonical summary.
4. **Hard annotation invariant.** The union of instance values `1..N` must equal semantic value
   `2` in all 46 instance frames. A mismatch exits `2`, names each affected frame and its
   extra/missing counts, and writes no output.
5. **Simple output publication.** JSON and report are rendered in memory, written to two
   temporary sibling files, and moved into place with `os.replace`. A normal failure before the
   replacements leaves the previous pair unchanged. A crash or replacement failure between the
   two replacements can leave a mixed pair; JSON is authoritative and check mode detects the
   mismatch. This narrow limitation is documented rather than hidden behind a journal.
6. **Small MVP surface.** No overlays, figures, review ledger, readiness report, artifact root,
   `.audit-staging/`, output manifest or transactional rollback machinery.

## Delivery Sequence

1. **Setup**: confirm runtime dependencies, package marker, Make targets and test skeleton.
2. **Foundation**: core records, exit codes, output policy, deterministic serializer, schema
   validation and CLI plumbing.
3. **Benchmark computation**: fingerprint/inventory, integrity, instance/semantic invariant,
   coverage, categories, scale, mapping, ROI, duplicates, credits, provenance, documented claims
   and limitations.
4. **Reporting and check**: render the 10-section report from validated JSON, implement
   generate/check, and test failure and output-policy behavior.
5. **Acceptance**: inspect a complete temporary-root run, run the first canonical generation and
   check, then run the quality gate and scope audit. Update the requirements matrix only after
   evidence exists.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Historical fingerprint cannot be reproduced | Regression test against the fixed value and counts; report mismatch as exit `2`; never replace the baseline |
| Annotation definitions drift | Pin half-open ROI semantics, order mapping, scale formulas and expected counts in research, schema and tests |
| Report and JSON disagree | Render only from validated JSON bytes; check mode re-renders and compares; no second calculation |
| A crash leaves a mixed pair | JSON is authoritative; check mode verifies the report's source digest and bytes; limitation documented |
| A failed run overwrites good evidence | All content is prepared in memory and temporary siblings; normal failures remove temporaries and leave old files |
| Output root is abused | Only two filenames; output root must exist; inside the repo only `docs/validation` is allowed; no subdirectories |
| Check mode depends on ignored artifacts | No overlays, figures or ledger in MVP; check needs only committed JSON and report |
| A scientific ambiguity is guessed | Documented claims, unresolved items and limitations are explicit; P0/G10 and ADR-0010 stay open |
| Notebook duplicates statistics | No notebook edit; static scope check in the final task |
| Matplotlib or TensorFlow leaks into the audit | No imports; fast tests and scope check enforce the boundary |

## Out of Scope

Selecting, downloading, surveying, ranking or recommending a normal-road source; creating a
class map, split, split hash or manifest; models, loaders, training, evaluation, thresholding,
inference or XAI; overlays, figures, visual review or readiness reporting; changing metrics,
ADRs, the constitution, `docs/dataset.md` or the requirements matrix before evidence.

## Extensions

- **EXT-01**: visual overlays and review ledger; see `contracts/visual-review-ledger.md`.
- **EXT-02**: aggregate figures rendered from the validated JSON.
- **EXT-03**: the `NR-01`–`NR-13` normal-road readiness gate; see
  `contracts/normal-road-readiness.md`.

Each extension requires a separate approved change, must not add fields to the MVP schema and
must not block the core audit.

## Complexity Tracking

No constitution violations. No additional service, artifact tree or abstraction layer is
introduced. The removed transaction, manifest, overlay, figure, ledger and readiness components
are deliberate simplifications.
