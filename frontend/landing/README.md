# `frontend/landing/` — Astro landing page

Owner: **M6**. **Status: `missing`** — this directory contains a README only.

Astro + Tailwind, static output, deployed to **Vercel**. The page explains the
project, shows only published results and links to the Streamlit prototype,
the technical report and the repository.

## Boundaries

- **No runtime API calls.** The landing page is static. It must not require the
  Minikube cluster to be running.
- **No invented metrics.** The build reads `docs/experiments/`; a model or metric
  appears only when its experiment file exists. Until then, the results section
  says the comparison is not published yet. Normal-road selection and
  RoadAnomaly held-out columns stay separate; the page never presents a single
  "best" number that hides the protocol.
- **No model assets.** The page may show a published figure from `assets/`, but
  it does not ship a SavedModel or call FastAPI.
- **Clear status language.** The site carries the same `implemented`,
  `in progress`, `missing` and `blocked` vocabulary as the README.

## Expected pages

| Route | Purpose |
|---|---|
| `/` | What the project does, current status, one published example (when available) |
| `/results` | Published comparison table and per-frame caveats; empty until experiments land |
| `/about` | Protocol, ADR-0001 evaluation-only caveat, credits |

The `Demo` link points at the public Streamlit URL configured at build time
(`PUBLIC_PROTOTYPE_URL`). There is no `/demo` route in the landing app.

## Commands

```bash
cd frontend/landing
npm ci
npm run dev       # http://localhost:4321
npm run build     # static output
```

Vercel builds this directory through its Git integration. CI runs the same
build when `package.json` exists.
