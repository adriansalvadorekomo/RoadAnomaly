# Feature Specification: Notebook workflow and learning clients

**Feature Branch**: `002-notebook-workflow`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "Preserve the template notebook, add five specialized notebooks,
keep authoritative logic in `dl/`, allow tagged toy concept checks, and record learning runs
separately."

## Context

`dl/notebooks/template_road_anomaly.ipynb` is the preserved teaching notebook. It contains
the ownership map, the CRISP-DM narrative, the evaluation protocol and the section-by-section
exercises. It is the entry point a new team member reads first.

The template currently mixes that teaching material with inline configuration, model, metric,
threshold and XAI stubs. [`dl/README.md`](../../dl/README.md) says notebooks contain no model
logic, while the requested suite needs a template plus five focused notebooks. That is a real
contract gap, not a documentation typo: without a written boundary, the notebooks become a
second implementation or a museum piece.

This feature defines two interfaces over **one implementation**:

| Interface | Purpose | Evidence status |
|---|---|---|
| Official (`dl/` + `make` targets) | Training, evaluation, thresholding, export and XAI for the project | Authoritative; records in `docs/experiments/` |
| Learning (template + five notebooks) | Explain concepts, inspect intermediate outputs, visualise results and run controlled exercises | Non-authoritative; learning records in `docs/experiments/learning/` |

The key decision is **annotated client notebooks**. A notebook may contain a short, clearly
tagged `concept-check` cell that demonstrates an idea on toy data. It may not contain an
authoritative model, training loop, metric, threshold selector, post-processor or XAI method.

This spec records the notebook contract only. It does not change the model lineup, the
evaluation protocol, the metric definitions, the threshold rule or the XAI gate. Those remain
in [ADR-0001](../../docs/adr/0001-evaluation-only-benchmark.md),
[ADR-0010](../../docs/adr/0010-model-lineup-and-evaluation-contract.md),
[`docs/metrics.md`](../../docs/metrics.md), [`docs/xai.md`](../../docs/xai.md) and the
[constitution](../../.specify/memory/constitution.md). A spec is a plan, not evidence; the
[requirements matrix](../../docs/validation/requirements-matrix.md) remains the status authority.

### Resolved decisions

- **D-002:** Notebooks are annotated clients. Tagged toy `concept-check` cells are allowed;
  authoritative logic stays in `dl/`.
- **D-003:** Learning-profile records live in `docs/experiments/learning/` and are excluded
  from the official index and from the README/report evidence chain.
- **D-004:** The first CI enforcement is static notebook-contract checking. Executing a tiny
  notebook smoke test is a later, optional slice.

## Terminology

- **Authoritative logic**: code that produces a published number, a selection, a threshold, a
  promotion decision, an exported model or XAI evidence.
- **Concept check**: a short, self-contained cell tagged `concept-check` that demonstrates one
  idea on toy tensors or scores. It is illustrative only, is never imported, and cannot feed an
  official result.
- **Official profile**: a run configured to follow the full provenance and evidence contract.
- **Learning profile**: a run intended for exploration or teaching. It is reproducible and
  recorded, but it is not evidence and cannot be promoted without an official rerun.

## User Scenarios & Testing

### User Story 1 - Follow the guided template (Priority: P1)

A new team member opens the preserved template and follows it from dataset comprehension to
evaluation, seeing the reasoning, the contract assertions and the intermediate outputs of the
same code the official command runs.

**Why this priority**: The template is the shared teaching artefact. Losing it, or letting it
drift into a parallel implementation, destroys the main onboarding path.

**Independent Test**: Open the template from the repository root. The role banner and ownership
map are visible; each section keeps its explanation; official cells import from `dl/`; no
authoritative function is defined inline after migration; toy demonstrations are tagged and
captioned.

**Acceptance Scenarios**:

1. **Given** a fresh checkout, **When** the learner opens the template, **Then** the banner says
   it is a non-authoritative teaching client and points to the notebook index and this spec.
2. **Given** a section that trains or evaluates a model, **When** the learner reads the code,
   **Then** the model, loss, training loop, metric, threshold and XAI calls come from `dl/`, and
   `inspect.getsource` or an equivalent inspection cell exposes the implementation.
3. **Given** a `concept-check` cell, **When** it is executed, **Then** it operates on toy data,
   uses `toy_`-prefixed names, writes no record and its variables are not consumed by an
   official cell.
4. **Given** a missing normal-road manifest, **When** the learner reaches training, **Then** the
   notebook stops with an actionable message and does not invent data, paths or results.

### User Story 2 - Keep official and learning runs separate (Priority: P1)

A team member can run an official experiment from the command line and a learning exercise from
a notebook without confusing the two evidence chains.

**Why this priority**: The project's evidence rule is a published number must trace to an
official experiment record. A notebook number must never be mistaken for that record.

**Independent Test**: Run an official config and a learning config. The official run writes a
record under `docs/experiments/`; the learning run writes under
`docs/experiments/learning/`; only the official record appears in the official index and can be
cited in the README or report.

**Acceptance Scenarios**:

1. **Given** an official config, **When** the operator runs the documented training or
   evaluation target, **Then** the run uses the pinned manifest and split hash, and writes an
   official experiment record.
2. **Given** a learning config, **When** a learner runs it from a notebook, **Then** the record
   says `Profile: learning`, lives under `docs/experiments/learning/`, and is not cited as
   published evidence.
3. **Given** a learning result worth promoting, **When** the team wants it in the report,
   **Then** they create an official config and rerun it; they do not copy the notebook number
   into the official record.

### User Story 3 - Use focused deep-dive notebooks (Priority: P2)

A learner can open one specialized notebook for dataset EDA, DeepLabV3+, the autoencoder, the
CNN/U-Net comparison or XAI, without reading a 100-cell template end to end.

**Why this priority**: The five deep dives make the material teachable in smaller sessions, but
they are useful only after the single-implementation boundary exists.

**Independent Test**: The suite contains `01_dataset_eda`, `02_deeplabv3plus`,
`03_autoencoder`, `04_cnn_unet` and `05_xai`. Each has a declared role, imports from `dl/`, and
covers only its named subject.

**Acceptance Scenarios**:

1. **Given** `01_dataset_eda`, **When** it inspects the 60 benchmark frames, **Then** it may
   inventory images, labels and coverage, but it does not train, fit, select or tune.
2. **Given** `02_deeplabv3plus`, `03_autoencoder` or `04_cnn_unet`, **When** the learner inspects
   the model-specific section, **Then** the architecture and intermediate tensors come from the
   corresponding `dl/models/` module, not from a notebook-local copy.
3. **Given** `05_xai`, **When** it renders heatmaps and faithfulness results, **Then** it calls
   `dl/evaluation/xai.py`, labels XAI as report-only, and never uses it for selection.

### User Story 4 - Enforce the notebook contract statically (Priority: P2)

A reviewer or CI can detect a notebook that duplicates authoritative logic or writes evidence
directly, without installing TensorFlow or executing the notebook.

**Why this priority**: Review alone cannot keep six notebooks from drifting. Static checks are
fast enough for the normal gate and do not require data or a GPU.

**Independent Test**: A notebook containing `def compute_f1(...)` outside a `concept-check`
cell, or writing to `docs/experiments/` directly, fails `make test`. A tagged toy cell using
`toy_softmax` passes.

**Acceptance Scenarios**:

1. **Given** a notebook that defines an official metric, model or XAI function outside a
   `concept-check` cell, **When** the static contract test runs, **Then** it fails with the
   notebook and cell identified.
2. **Given** a notebook that writes an experiment record directly instead of calling the shared
   writer, **When** the static contract test runs, **Then** it fails.
3. **Given** a notebook whose `concept-check` variables are referenced by a non-concept cell,
   **When** the static contract test runs, **Then** it fails.
4. **Given** only documentation changes, **When** `make lint type test` runs, **Then** the
   notebook checks add no TensorFlow import and no data dependency.

### Edge Cases

- **Template during migration**: the preserved template still contains legacy inline stubs.
  Until the extraction lands, its banner and metadata mark it non-authoritative. The static
  contract test is enabled when the inline authoritative logic has moved, so the gate is never
  made green by a permanent allowlist.
- **No manifest or dataset**: notebooks fail clearly and stop. They must not generate substitute
  frames, labels, split hashes or results.
- **Benchmark temptation**: a notebook may inspect and score the 60 frames with a fixed rule,
  but it may not fit weights, choose a model, select a threshold or promote an alias on them.
- **Concept check leaks**: a toy score map used by a later official cell is a contract violation,
  even if the toy cell is correctly tagged.
- **Presentation helpers**: `plot_*`, `show_*` and `display_*` helpers are allowed because they
  present outputs; they must not compute an official metric or alter a score map.
- **Notebook imports**: one notebook importing another with `%run`, `import` or a copied module
  is forbidden. Shared code belongs in `dl/`.
- **Offline or CPU-only work**: a learner may inspect saved outputs without a GPU; a full
  training run still needs explicit approval and a pinned manifest.
- **Committed outputs**: executed outputs are stripped before commit; a committed notebook has
  no images, logs or absolute paths.

## Requirements

### Functional Requirements

- **FR-001**: The repository MUST preserve
  `dl/notebooks/template_road_anomaly.ipynb` at its current path. It MUST NOT be deleted,
  silently replaced or reduced to a link.
- **FR-002**: The template MUST remain the central guided tour. Its ownership map, CRISP-DM
  narrative, contract assertions, section exercises and useful experiments MUST be retained
  during migration.
- **FR-003**: The specialized suite MUST use these stable names: `01_dataset_eda`,
  `02_deeplabv3plus`, `03_autoencoder`, `04_cnn_unet` and `05_xai`. A separate
  `04_comparison` notebook is not required; comparison lives in the template's end-to-end
  section and the official evaluation output.
- **FR-004**: Every notebook MUST declare its role in notebook metadata:
  `roadanomaly.role` is `template` or `specialized`, `roadanomaly.authoritative` is `false`, and
  `roadanomaly.contract` points to this spec.
- **FR-005**: Authoritative model, training, metric, threshold, post-processing and XAI logic
  MUST live in `dl/`. Notebooks MUST import it rather than reimplement it.
- **FR-006**: A notebook MAY contain a `concept-check` cell only when it is tagged
  `concept-check`, uses `toy_`-prefixed names for definitions and persistent variables, is
  captioned as illustrative only, writes no record, and is not imported or consumed by another
  cell.
- **FR-007**: Outside tagged `concept-check` cells, notebooks MUST NOT define authoritative
  functions, including `build_*`, `train_*`/`fit_*`, `compute_*`, `evaluate_*`,
  `select_threshold`, `postprocess_mask`, `seg_gradcam`, `integrated_gradients`, `auroc`,
  `aupro`, `hd95`, `boundary_iou`, `dice` or `iou`. Presentation helpers (`plot_*`, `show_*`,
  `display_*`) remain allowed.
- **FR-008**: Notebooks MUST NOT write experiment evidence directly. They MUST call the shared
  experiment-record API (eventually `dl.evaluation.experiment`) and pass the selected profile.
- **FR-009**: Run configurations MUST declare `profile: official` or `profile: learning`.
  Official runs require the pinned normal-road manifest, scene-grouped split hash, seed and
  config hash. Learning runs must still be reproducible but are not official evidence.
- **FR-010**: Learning-profile records MUST live under `docs/experiments/learning/`, MUST
  declare `Profile: learning`, and MUST NOT appear in the official experiment index, README or
  report. Promoting a learning result requires an official config and a fresh official run.
- **FR-011**: RoadAnomaly MUST remain evaluation-only in every notebook. No notebook may fit
  weights, early-stop, select a model, choose an operating threshold, promote an alias or tune
  any parameter on the 60 frames. `01_dataset_eda` may inspect them; evaluation notebooks may
  score them with a rule fixed on normal-road validation.
- **FR-012**: The first notebook CI enforcement MUST be static. It MUST parse notebook JSON and
  code cells, MUST NOT execute notebooks and MUST NOT require TensorFlow, a GPU or the dataset.
  A tiny smoke execution is explicitly deferred.
- **FR-013**: The template migration MUST replace inline authoritative stubs with calls into
  `dl/`, `inspect.getsource` or equivalent source walkthroughs, and intermediate-tensor or
  intermediate-output inspection cells. It MUST NOT preserve the template's current binary
  training target; the target is multi-class normal-road labels per ADR-0010.
- **FR-014**: Notebooks MUST NOT import or `%run` another notebook. Shared code belongs in
  `dl/`.
- **FR-015**: The notebook suite MUST NOT add a runtime container, deployment component or C4
  relationship. Notebooks are development interfaces, not production services.
- **FR-016**: `dl/README.md` and `dl/notebooks/README.md` MUST map all six notebooks, state the
  official/learning split, and link this spec.
- **FR-017**: Notebooks MUST keep `data/` and `data/credits.txt` unmodified. Figures that use
  benchmark frames MUST carry the attribution required by the dataset licence.
- **FR-018**: Notebooks MUST use repository-relative paths, contain no secrets or absolute home
  paths, and be committed with outputs cleared.

### Key Entities

- **Notebook role**: the metadata block that identifies a notebook as `template` or
  `specialized`, marks it non-authoritative, and links this contract.
- **Concept-check cell**: a tagged, toy-only cell with `toy_`-prefixed names and no evidence
  side effects.
- **Run profile**: `official` or `learning`; decides the required provenance and the evidence
  directory.
- **Experiment record**: the Markdown record copied from
  `docs/experiments/0000-template.md`; its profile and location determine whether it is
  official evidence.
- **Learning record**: a record under `docs/experiments/learning/` that is reproducible but
  cannot be cited as a published number.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A deliberately duplicated official function in a notebook (for example
  `def compute_f1`) makes the static notebook contract test fail outside a `concept-check`
  cell; removing it makes the test pass.
- **SC-002**: A notebook that writes to `docs/experiments/` directly fails the contract test;
  a notebook that calls the shared writer passes.
- **SC-003**: Every notebook has `roadanomaly.role`, `roadanomaly.authoritative: false` and a
  contract link; a missing role fails the test.
- **SC-004**: `git grep` finds each official metric or XAI implementation only in its single
  `dl/` module (plus tests); after migration, `dl/notebooks/` contains no authoritative
  definition.
- **SC-005**: Every learning record has `Profile: learning` and lives under
  `docs/experiments/learning/`; the official index contains zero learning records.
- **SC-006**: No learning number is cited in `README.md` or `docs/report/`; a citation without
  an official record is treated as a bug.
- **SC-007**: `make lint type test` enforces the static notebook checks without importing
  TensorFlow or reading `data/`; the optional smoke execution remains a separate target.
- **SC-008**: The template's section structure and ownership map remain intact after migration;
  no section is silently deleted, and every removed code cell has a corresponding `dl/` home.
- **SC-009**: The notebook suite adds no C4 container and no deployment dependency; the
  architecture tests still pass unchanged.

## Assumptions

- A normal-road manifest and scene-grouped split will exist before the training path is
  executable; until then, notebooks may be read and inspected but cannot honestly train.
- The `dl/` modules (`config.py`, `data/`, `models/`, `training/`, `evaluation/`,
  `inference/`) will expose stable callable APIs before the template is fully refactored.
- Static notebook checks can be implemented with the standard library's JSON and AST support;
  no new notebook execution dependency is required for the first slice.
- Notebook users have a Jupyter environment with the pinned dependencies; a full training run
  remains an explicit, approved operation.
- The official evidence chain remains `docs/experiments/`; notebooks are learning tools, not a
  second publication channel.

## Dependencies

- The normal-road manifest and scene-grouped split feature (the proposed
  `001-normal-road-manifest`) and gap G10 in the requirements matrix.
- ADR-0010's multi-class training contract and the resolution of the scientific P0 findings
  around AUROC/AUPRO placement, RoadAnomaly scoring and the threshold protocol.
- The shared `dl/` implementations of models, training, metrics, thresholding and XAI.
- The experiment-record profile and the `docs/experiments/learning/` convention.
- The existing static architecture tests and `make lint type test` gate.

## Out of Scope

- Implementing the models, training loop, metrics, threshold selector, XAI methods or
  experiment-record API.
- Fixing the unresolved scientific P0 defects in the template or the evaluation protocol.
- Running a full training, evaluation or XAI campaign.
- A separate `04_comparison` notebook, a hosted notebook service or a new C4 container.
- A notebook smoke execution in the first CI slice.
- Replacing an ADR or amending the constitution. No new ADR is needed for this feature because
  it does not change a public contract or an invariant.

## Review Checklist

- [ ] The template's teaching material and ownership map are preserved.
- [ ] The five specialized names match the stable suite.
- [ ] Every notebook declares its role and non-authoritative status.
- [ ] Official functions exist only in `dl/`; concept checks are tagged, toy-only and contained.
- [ ] Learning records live under `docs/experiments/learning/` and never enter the official
      index.
- [ ] No notebook trains, selects or promotes on RoadAnomaly's 60 frames.
- [ ] Static checks run without TensorFlow, a GPU or the dataset.
- [ ] No new C4 container or deployment component is introduced.
