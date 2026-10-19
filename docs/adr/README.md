# Architecture and experiment decisions

Short records of decisions that are expensive to reverse, kept next to the
code so nobody has to reconstruct the reasoning from a group chat.

| ID | Decision | Status |
|---|---|---|
| [0001](0001-evaluation-only-benchmark.md) | Treat RoadAnomaly as an evaluation-only benchmark | Accepted |
| [0002](0002-three-model-families.md) | Compare three model families, not one | Accepted |
| [0003](0003-monorepo-and-serving-stack.md) | Monorepo, FastAPI + Next.js, GHCR delivery | Accepted; deployment clause superseded by 0004 |
| [0004](0004-vercel-and-gitops-deployment.md) | Vercel frontend, Kubernetes + Argo CD inference target | Accepted (not implemented) |

## Adding one

Copy `0000-template.md`, number it, open a pull request. An ADR that nobody
disagreed with is fine to merge immediately; an ADR that reverses an earlier
one should say so explicitly at the top ("Supersedes ADR-0002").
