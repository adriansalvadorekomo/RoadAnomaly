# 0012. Use Structurizr DSL as the architecture source of truth

- **Status:** Accepted (tooling; diagrams are target-state)
- **Date:** 2026-10-21
- **Deciders:** whole team
- **Supersedes:** the archify-based diagram source and generated HTML/PNG assets

## Context

The repository previously kept a custom `docs/architecture/architecture.json`
spec and generated a large interactive `architecture.html` plus two README PNGs
with archify. The map was useful, but it encoded a CRISP-DM flow rather than a
C4 model, coupled the architecture tests to one tool's JSON schema, and produced
a generated HTML page that was hard to review and easy to let drift.

The documentation now needs a standard, maintainable C4 model with a single
source of truth, rendered PNGs committed for GitHub, and no duplicate diagram
definitions. Structurizr DSL provides the model, views and relationships; the
Structurizr renderer produces the diagrams. The repository does not need an
interactive generated HTML artifact.

## Decision

1. `docs/architecture/workspace.dsl` is the single source of truth for the C4
   model. Do not create a second architecture JSON, Mermaid flow or hand-edited
   diagram.
2. The committed views are:
   - **C1 system context** — the RoadAnomaly system, its actors and the
     external normal-road/pretrained-weights/CI dependencies.
   - **C2 offline pipeline** — dataset and contracts, normal-road manifest,
     training, model artifacts, validation/selection, benchmark evaluation,
     XAI and the model registry.
   Online inference and deployment views are added only when API/UI/container
   files exist.
3. Implemented and planned elements are tagged in the DSL. The C2 view is a
   target-state view; the README says so and does not imply that planned
   containers are running.
4. PNGs are rendered from the DSL into `docs/architecture/diagrams/` with a
   pinned Structurizr CLI static-site export and headless Chromium. The CLI does
   not export PNG directly; the official Structurizr workflow is a browser.
   No generated HTML is committed. The exact command is recorded in
   `docs/architecture/README.md` and `render.sh`.
5. The architecture contract tests validate the DSL's required views, status
   tags, promotion guardrails and committed PNGs. CI validates the DSL with
   Structurizr. Rendering stays a local/manual documentation step unless it is
   proven fast enough for CI.
6. The old archify JSON, HTML and README PNGs are deleted. Their references are
   removed from README, AGENTS, docs and tests.

## Consequences

**What gets easier.** The model is readable, diffable and standard C4. A
reviewer can inspect one DSL file and see why each container and relationship
exists. The README embeds ordinary PNGs instead of a generated interactive
page. The tests check architecture meaning without depending on archify's
schema.

**What gets harder.** Rendering needs Java, Chromium and the pinned Structurizr
CLI download. Structurizr's automatic layout still needs visual review for
overlaps. C4 does not express CRISP-DM phases directly; the phase mapping
remains a table in `docs/architecture/README.md` and ADR-0007 rather than a
second diagram.

**What we lose.** The interactive HTML, guided tours and dark-mode PNG variants
are removed. If an interactive view is needed later, Structurizr Lite can serve
the DSL locally; generated HTML is still not committed.

## Alternatives considered

| Option | Why not |
|---|---|
| Keep archify and add Structurizr | Two sources of truth; guaranteed drift |
| Keep archify only | Does not meet the C4 requirement and keeps the custom schema/tests |
| Use Mermaid as the source | No standard C4 model; manual layout and duplicate definitions |
| Commit generated Structurizr HTML | Large generated artifact; the PNGs are the README contract |
| Hand-edit the PNGs | Not reproducible; the source would no longer be authoritative |

## How we would know this was wrong

If the pinned Structurizr renderer cannot produce readable C1/C2 PNGs, or if
the C4 model cannot express the benchmark-to-registry guardrail without
misleading relationships, the tooling decision is reopened. The guardrail is
not weakened to fit the renderer.
