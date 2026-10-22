# 0013. Adopt spec-driven development for feature work

- **Status:** Accepted
- **Date:** 2026-10-22
- **Deciders:** repository owner
- **Supersedes:** none

## Context

The repository has a methodology (CRISP-DM, [ADR-0007](0007-crisp-dm-methodology.md)),
an evidence bar ([requirements matrix](../validation/requirements-matrix.md)),
normative metric and XAI contracts, and a model/evaluation decision in
[ADR-0010](0010-model-lineup-and-evaluation-contract.md). It does not have a
per-feature workflow. Model, training, evaluation and serving code is still
missing, so the next work is a sequence of features that need a written intent,
a plan and checkable tasks before code lands.

Spec Kit 1.2.2 with the OpenCode integration is installed locally. Its generated
workspace, commands and templates make the spec → plan → tasks → implement loop
available without adding a second package ecosystem or a hosted service.

The obvious option — keep the workflow local and undocumented — would make the
method invisible to the repository, unreproducible on a fresh clone and easy to
abandon halfway through the project.

## Decision

1. Non-trivial feature work starts with a spec in `specs/NNN-kebab-name/`, using
   the Spec Kit commands documented in [`docs/sdd.md`](../sdd.md).
2. `.specify/` and the generated `.opencode/commands/speckit.*.md` entry points
   are tracked. Personal agent state under `.opencode/` and `.commandcode/` is
   ignored. The `.opencode` exception is limited to the generated SDD commands.
3. SDD is the per-feature loop. CRISP-DM remains the project lifecycle, ADRs
   remain the place for irreversible decisions, `docs/experiments/` remains the
   only home for run evidence, and the requirements matrix remains the status
   authority. A spec never promotes a requirement to `implemented`.
4. The Spec Kit constitution is committed as generated. It is not authored or
   treated as normative in this decision; `AGENTS.md` and the ADRs remain the
   project rules until a separate decision says otherwise.
5. A spec that depends on a model, metric or evaluation rule links the relevant
   ADR or contract instead of restating it. The first suggested feature is the
   normal-road manifest and loader (see `docs/sdd.md`).

## Alternatives considered

| Option | Why not |
|---|---|
| Keep Spec Kit local and untracked | The workflow would not exist on a fresh clone; `init-options.json` and the integration manifest would describe files the repository does not contain |
| Track `.specify/` but not the generated commands | The OpenCode integration is half-installed: the configuration is present but `/speckit.*` is missing |
| Write a project constitution now | The constitution is a principles document; this change adapts the repository to SDD and must not invent the project's principles. The existing rules already live in `AGENTS.md` and the ADRs |
| Use ad-hoc feature notes in `docs/` | No fixed artifact set, no ordered tasks, and no clear separation between a plan and the experiment evidence |

## Consequences

**What gets easier.** Each feature has a written intent, a plan and an ordered
task list before code lands. A fresh clone can run the same `/speckit.*` commands.
Specs can be reviewed without reading an implementation, and the link from a
feature to its ADR, metric contract or experiment is explicit.

**What gets harder.** There is another artifact set to keep current. Spec Kit
upgrades rewrite `.specify/`, so a version bump produces a reviewable but
non-trivial diff. Contributors must resist treating a checked task or a spec as
proof that a requirement is implemented.

**How we would know this was wrong.** Specs accumulate without corresponding
code or tests; contributors routinely bypass the workflow because it adds no
review value; or a spec is used to justify a benchmark-selected model or a
published number without an experiment record. Any of those reopens this ADR.
