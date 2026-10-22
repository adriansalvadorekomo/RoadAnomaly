# Feature specs

One directory per feature, sequential and kebab-cased:

```text
specs/001-normal-road-manifest/
├── spec.md
├── plan.md
├── tasks.md
└── ...
```

Specs are created with the Spec Kit commands documented in
[`docs/sdd.md`](../docs/sdd.md) and decided in
[ADR-0013](../docs/adr/0013-spec-driven-development.md):

```text
/speckit.specify  →  /speckit.plan  →  /speckit.tasks  →  /speckit.implement
```

Do not create a spec for a typo, a chore or a documentation-only change. Do not
use a spec as evidence that a requirement is `implemented`; status comes from the
[requirements matrix](../docs/validation/requirements-matrix.md), and published
numbers come from [`docs/experiments/`](../docs/experiments/).

The active feature pointer (`.specify/feature.json`) is machine-local and
ignored. Commit the feature directory itself.
