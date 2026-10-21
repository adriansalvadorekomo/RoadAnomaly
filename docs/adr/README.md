# Architecture and experiment decisions

Short records of decisions that are expensive to reverse, kept next to the
code so nobody has to reconstruct the reasoning from a group chat.

| ID | Decision | Status |
|---|---|---|
| [0001](0001-evaluation-only-benchmark.md) | Treat RoadAnomaly as an evaluation-only benchmark | Accepted; metric contract amended by 0010 |
| [0002](0002-three-model-families.md) | Compare three model families, not one | Superseded by 0010 |
| [0003](0003-monorepo-and-serving-stack.md) | Monorepo, FastAPI serving, GHCR delivery | Accepted; deployment clause superseded by 0004; serving artifact clause superseded by 0005; frontend clause superseded by 0006 |
| [0004](0004-vercel-and-gitops-deployment.md) | Vercel frontend, Kubernetes + Argo CD inference target | Accepted (not implemented); inference runtime amended by 0005 |
| [0005](0005-tensorflow-framework.md) | TensorFlow/Keras for training and inference | Accepted; model-family clause amended by 0010 |
| [0006](0006-astro-and-streamlit-frontend.md) | Astro landing page + Streamlit prototype; FastAPI backend | Accepted (not implemented) |
| [0007](0007-crisp-dm-methodology.md) | Use CRISP-DM as the project methodology | Accepted; current references in 0010–0012 |
| [0008](0008-promotion-and-model-registry.md) | Select on normal-road validation; immutable registry and GitOps promotion | Accepted (not implemented); IDs and scorecard amended by 0010 |
| [0009](0009-xai-evaluation-gate.md) | XAI is an evaluation gate | Accepted; methods selected by 0011 |
| [0010](0010-model-lineup-and-evaluation-contract.md) | Model lineup and evaluation contract | Accepted (target state; not implemented) |
| [0011](0011-xai-methods-and-faithfulness.md) | XAI methods and faithfulness checks | Accepted (methods selected; not implemented) |
| [0012](0012-structurizr-c4-architecture.md) | Use Structurizr DSL as the architecture source of truth | Accepted (tooling; target diagrams) |

## Adding one

Copy `0000-template.md`, number it, open a pull request. An ADR that nobody
disagreed with is fine to merge immediately; an ADR that reverses an earlier
one should say so explicitly at the top ("Supersedes ADR-0002").
