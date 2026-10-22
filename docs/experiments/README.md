# Experiment log

One file per run set. **Every number in the README and the report must trace
back to an official file here.** A metric with no experiment file behind it is a
bug.

Official records live at this level. Learning-profile records live in
[`learning/`](learning/) and are not evidence for a published number. Every
record declares `Profile: official` or `Profile: learning`; the profile decides
which evidence chain it belongs to.

For an official record, copy `0000-template.md`, number it in order, and open a
pull request. For a learning record, copy it into [`learning/`](learning/) and
keep the learning profile. The pull request template asks whether your change
can affect a reported number; if it can, this directory is where the new number
is justified.

## Official index

| ID | Date | Model | One-line finding |
|---|---|---|---|
| _(empty — week 1)_ | | | |

Learning records are never listed here. They live under
[`learning/`](learning/) and cannot be cited in the README or report without an
official rerun.

## Why files and not a spreadsheet

Because an experiment is only useful if it records what was *assumed* as well as
what was measured. The template asks for the hypothesis and for the result that
would have falsified it, which is the part that gets lost first. It also forces
normal-road **selection** metrics and held-out **RoadAnomaly** scores into
separate rows: they are different evidence and must never be averaged together.
