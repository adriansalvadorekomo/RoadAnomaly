# 0009. XAI is an evaluation gate; the method remains open

- **Status:** Accepted (placement and gate); method decision `blocked` (G1)
- **Date:** 2026-10-19
- **Deciders:** whole team

## Context

The technical validation requires an XAI implementation and a written
justification (V1.8). The previous architecture, ADR-0002 and the roadmap did
not place XAI anywhere, so a model could land and the requirement would still
have no owner, input or evidence format. The method cannot be chosen yet
because no model exists and the team has not compared faithfulness, cost and
TensorFlow support.

Leaving XAI as a UI feature would be wrong: it is evidence that the selected
model's decisions are inspectable, not a decorative panel. Leaving it
unmentioned would make V1.8 `missing` even after the model lands.

## Decision

1. **Placement.** XAI belongs to CRISP-DM phase 5, Evaluation. It consumes the
   **selected** model and its score maps on evaluation frames. It does not
   consume the benchmark to choose a model, and it does not alter weights,
   thresholds or the selected alias.
2. **Gate.** V1.8 stays `blocked` on **G1: no method chosen**. Before
   implementation, the team must record a method decision (a new ADR or a
   dated addendum to this one) that states:
   - the method and why it fits the selected model family;
   - what is explained (per-pixel score, region, or whole frame);
   - the faithfulness check and the baseline it is compared with;
   - the compute and UI cost;
   - how the explanation is stored and linked to the model digest.
3. **Candidates, not a decision.** Grad-CAM, occlusion sensitivity, integrated
   gradients and plain saliency are all plausible. Naming them here does not
   select one.
4. **Evidence format.** Each XAI run must produce per-frame explanation
   artifacts, a short written interpretation and a link to the experiment
   record. The Streamlit prototype may display them only when they exist; it
   must not render a placeholder explanation.
5. **No promotion right.** XAI results are report-only. They never appear in
   `selected.json` and never gate a release. They are part of the evaluation
   evidence, not a second selection metric.

## Alternatives considered

| Option | Why not |
|---|---|
| Implement XAI as a Streamlit-only feature | Produces a visual with no evaluation record or justification; V1.8 asks for both |
| Pick Grad-CAM now because it is popular | No model exists to check that the explanation is faithful or even applicable to the chosen architecture |
| Implement several methods and compare | Useful later, but three models plus a comparison plus deployment is already the critical path |
| Leave XAI out of the architecture until a method is chosen | The requirement then has no owner or integration point, which is how it went missing before |

## Consequences

**What gets easier.** V1.8 has a defined place, a named dependency and an
evidence format. The prototype can add an explanation panel without redefining
the API contract or the promotion rule.

**What gets harder.** The team must make and justify a method decision after a
model exists, then implement and evaluate it. That is real work on the critical
path, not a documentation task.

**How we would know this was wrong.** If the selected model cannot expose
useful gradients or region-level scores, or if the explanation method cannot be
checked against a baseline within the remaining compute budget, the method
decision must be reopened rather than shipping an unverified visual.
