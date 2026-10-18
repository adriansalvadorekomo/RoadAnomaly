# `frontend/` — anomaly dashboard

Owner: **M6**. Next.js (App Router) + Tailwind + shadcn/ui.

## What it has to do in three clicks

1. Drop in a road image (or pick one of the 60 bundled examples).
2. See the anomaly mask overlaid on the image, plus the raw score heatmap.
3. Compare the three methods side by side, with the numbers from
   `docs/experiments/` shown next to the picture.

## Screens

| Route | Purpose |
|---|---|
| `/` | Landing: what the project does, headline metrics, one example |
| `/demo` | Upload / pick a sample, run inference, overlay + heatmap |
| `/compare` | Same frame through all three models, score table |
| `/about` | Method summary, dataset caveats (ADR-0001), credits |

## Rules

- **Types come from the API.** Regenerate from the backend's OpenAPI schema;
  do not hand-write response shapes.
- **Never fake a result.** If the API is unavailable, say so. A placeholder
  mask that happens to look plausible is worse than an error state.
- Sample images are the bundled evaluation frames. They are evaluation data,
  and the UI says so.
