# Lightweight Dagster — Size Reduction Results

Measured with `compact_tools/measure.sh` against the project `.venv` site-packages.
Acceptance test: `compact_tools/acceptance_test.py` (3 dependent assets + `materialize()`).

## Phase 0 — Baseline (core editable install, no webserver/graphql)

- **Total site-packages: 120M**
- Acceptance test: PASS

Top dagster-attributable contributors:

| Package | Size | Targeted by |
|---|---|---|
| grpc | 39M | Approach 3 — replace with in-process |
| sqlalchemy | 18M | Approach 3 — replace with stdlib sqlite3 |
| pygments (via rich) | 9.2M | trim |
| pydantic + pydantic_core | 8.3M | core dep (keep) |
| pytz | 2.7M | replace with stdlib zoneinfo |
| google/protobuf | 2.7M | Approach 3 — drops with grpc |
| tzdata | 2.6M | keep (zoneinfo data) |
| alembic | 2.4M | Approach 3 — drops with sqlalchemy |
| antlr4 | 1.1M | Approach 3 — hand-written parser |

Notes:
- `pip` (12M) is venv tooling, not dagster — excluded from dagster footprint.

## Phase 1 — Approach 1: delete unnecessary packages from the fork

Deleted from `python_modules/`: `dagster-webserver`, `dagster-graphql`,
`dagster-cloud`, `dagit`, `dagster-test`, `automation`, and 69 of 70 entries in
`libraries/` (kept only `dagster-shared`). ~155M of fork source removed.

- Acceptance test: PASS
- site-packages: unchanged (these were never installed). The 42M webserver win
  is realized by *not installing* it — Approach 1's payoff is at the
  distribution/install boundary, not in an already-minimal install.

## Phase 2a — Approach 3: remove gRPC stack

Finding: `grpcio`, `grpcio-health-checking`, `protobuf` are **already lazily
imported** — not loaded by `import dagster` nor during `materialize()`. Removed
them and moved to an optional `grpc` extra in `pyproject.toml`.

- **Total site-packages: 120M → 79M (−41M)**
- Acceptance test: PASS
- Restore the gRPC code server with `pip install dagster[grpc]`.

## Phase 2b — Approach 3: replace antlr4 with hand-written parser

Replaced the ~6,200-line antlr4-generated asset-selection parser with a
dependency-free recursive-descent parser
(`antlr_asset_selection/lightweight_parser.py`). Cross-validated against the
original antlr parser on 48 selection strings (boolean ops, traversals,
functions, all attribute exprs) — **48/48 identical behavior**. Removed
`antlr4-python3-runtime` dependency and the generated parser files.

- **Total site-packages: 79M → 78M (−1.1M)**
- Acceptance test: PASS; `AssetSelection.from_string()` still works.

## Phase 3 (planned) — Approach 3: SQLAlchemy/alembic → stdlib sqlite3

Remaining large target: `sqlalchemy` (18M) + `alembic` (2.4M) + `Mako` (~0.75M).
These ARE imported during `materialize()` (ephemeral run/event-log storage).
Requires reimplementing the `RunStorage` / `EventLogStorage` ABCs on stdlib
`sqlite3` and replacing alembic migrations with a versioned schema bootstrap.
Largest/riskiest remaining task.

## Running tally (site-packages, incl. 12M pip tooling)

| Stage | site-packages | vs brief 140M baseline |
|---|---|---|
| Brief baseline (with webserver) | 140M | — |
| Phase 0 (core install, no webserver) | 120M | −14% |
| Phase 2a (no grpc) | 79M | −44% |
| Phase 2b (no antlr4) | 78M | −44% |
| Phase 3 target (no sqlalchemy) | ~57M | −59% |
- Editable install: dagster's own ~20M core source is symlinked, not copied into
  site-packages, so it is not counted above. Measure core-source reductions from
  `python_modules/dagster/dagster` directly.
- Brief's 140M baseline included `dagster-webserver` (42M, compiled React UI),
  which we never install here — that is the Approach 1 win, already realized by
  not installing the webserver/graphql packages.
