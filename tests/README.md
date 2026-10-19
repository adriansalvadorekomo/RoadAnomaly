# `tests/` — what each tier covers

Four tiers, named for what they need to run. The dataset and architecture tiers
exist today; the other two appear with the code that makes them meaningful.

| Directory | Scope | Needs | Status |
|---|---|---|---|
| `dataset/` | The tracked RoadAnomaly checkout: frame ↔ label contract, mask vocabulary, instance consistency | numpy + Pillow, no GPU | **implemented** — 6 tests |
| `architecture/` | The committed architecture spec: unique IDs, six CRISP-DM regions, no benchmark-to-registry path, XAI gate, PNG asset dimensions | stdlib + Pillow, no archify | **implemented** — 6 tests |
| `unit/` | Pure functions: metrics, mask decoding, thresholding | no dataset, no GPU | **missing** — appears with the first model module |
| `integration/` | API contracts, artifact loading, end-to-end inference | an exported artifact | **missing** — appears with the backend |

`conftest.py` holds the shared path fixtures (`data_dir`, `frame_names`,
`label_dirs`); every tier inherits them.

```bash
make test          # everything
make data-check    # only the dataset contract (fast, no GPU)
```

A directory that does not exist yet is listed on purpose: this file says
where the first test of each tier goes. It is not a claim that the tier is
implemented.
