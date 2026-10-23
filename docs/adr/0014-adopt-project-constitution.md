# 0014. Adopt the RoadAnomaly project constitution as normative

- **Status:** Accepted
- **Date:** 2026-10-22
- **Deciders:** whole team
- **Supersedes:** [ADR-0013](0013-spec-driven-development.md) decision 4 only
- **Related:** [ADR-0001](0001-evaluation-only-benchmark.md),
  [ADR-0008](0008-promotion-and-model-registry.md),
  [ADR-0010](0010-model-lineup-and-evaluation-contract.md)

## Context

The repository installed Spec Kit 1.2.2 and adopted SDD in
[ADR-0013](0013-spec-driven-development.md). At that time the generated
constitution was a placeholder, so decision 4 kept it non-normative and left
`AGENTS.md` and the ADRs as the project rules.

A project-authored constitution now exists in `.specify/memory/constitution.md`.
It records the project hierarchy, the evaluation-only guardrail, the model and
scoring contract, reproducibility requirements, the evidence bar and the quality
rules. Leaving ADR-0013 decision 4 and `docs/sdd.md` unchanged would preserve two
contradictory authority models: a supreme constitution in `AGENTS.md` and a
non-normative template in the SDD documents.

## Decision

1. The text in `.specify/memory/constitution.md`, version 1.0, is the project
   constitution and is normative.
2. Precedence is **constitution > accepted ADRs > `AGENTS.md` > specs**. The
   requirements matrix remains the authority for requirement status; domain
   contracts such as `docs/metrics.md`, `docs/xai.md` and `docs/dataset.md`
   remain normative within their scope.
3. ADR-0013 decision 4 is superseded only to the extent that it says the
   constitution is generated and non-normative. The rest of ADR-0013, including
   the SDD loop, remains in force.
4. Amendments to the constitution require a new ADR, as stated in constitution
   rule 1.
5. `docs/sdd.md` and the ADR index must point to this decision. The constitution
   and `AGENTS.md` are committed together so the hierarchy and the agent rules
   cannot drift apart.

## Alternatives considered

| Option | Why not |
|---|---|
| Keep the generated constitution and leave it non-normative | Preserves the contradiction with `AGENTS.md`; agents would still inherit two different authority models |
| Keep the project constitution as a subordinate principles summary | Avoids a new ADR but contradicts constitution rule 1 and the hierarchy in `AGENTS.md` |
| Revert the working-tree constitution to the Spec Kit template | Loses the project-specific rules that `AGENTS.md` already treats as governing and leaves no single principles document |

## Consequences

**What gets easier.** Every agent and contributor has one hierarchy to resolve
conflicts. The `/speckit.*` workflow reads a real project constitution instead of
a placeholder. Invariant changes now have a clear route through an ADR.

**What gets harder.** Constitution amendments require an ADR. `docs/sdd.md`, the
ADR index and `AGENTS.md` must stay aligned when the governance text changes.

**How we would know this was wrong.** Specs or ADRs routinely bypass the
constitution; the constitution duplicates the ADRs and drifts; or contributors
cannot tell which document wins a conflict. Any of those reopens this ADR.
