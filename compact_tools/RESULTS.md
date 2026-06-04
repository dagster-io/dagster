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

## Phase 3 — Approach 3: SQLAlchemy/alembic → stdlib sqlite3  ✅

Reimplemented the `RunStorage` and `EventLogStorage` ABCs directly on stdlib
`sqlite3` (`dagster/_core/storage/lightweight/sqlite3_run_storage.py`,
`sqlite3_event_log_storage.py`) and routed the ephemeral instance to them
(`_core/instance/factory.py`). Hot path (events, runs, snapshots, asset records,
latest materializations, tags, dynamic partitions) is fully implemented;
daemon/server-only features (concurrency, backfills, asset checks, heartbeats)
are no-op/empty stubs.

To uninstall sqlalchemy entirely, made several eager imports lazy so neither
`import dagster` nor `materialize()` pulls it:
- `storage/event_log/__init__.py`, `runs/__init__.py`, `schedules/__init__.py`:
  SQLAlchemy-backed classes now load via module `__getattr__`.
- `AlembicVersion` (a pure type alias) defined locally in the storage ABCs +
  `legacy_storage.py` instead of importing from the sqlalchemy-heavy `storage/sql.py`.
- `telemetry.py`: `SqlRunStorage` import moved into the telemetry-enabled branch.

Moved `sqlalchemy` + `alembic` to an optional `sql` extra. Removed
`sqlalchemy`/`alembic`/`Mako` from the venv.

- **Total site-packages: 78M → 57M (−21M)**
- Acceptance test: PASS; run/event/asset read paths verified; `sqlalchemy`
  confirmed absent (`import sqlalchemy` → ModuleNotFoundError).
- Restore SQL-backed storage with `pip install dagster[sql]`.

## Updated tally (site-packages, incl. 12M pip tooling)

| Stage | site-packages | vs brief 140M baseline |
|---|---|---|
| Brief baseline (with webserver) | 140M | — |
| Phase 0 (core install, no webserver) | 120M | −14% |
| Phase 2a (no grpc) | 79M | −44% |
| Phase 2b (no antlr4) | 78M | −44% |
| Phase 3 (no sqlalchemy) | **57M** | **−59%** |

## Phase 5 — drop rich/pygments  ✅

`rich` had ZERO imports anywhere in dagster source — it was pulled in only by
structlog's optional rich-traceback support (`try: import rich except ImportError`).
Removed `rich` from deps; that also dropped `pygments` (9.2M), `markdown-it-py`,
`mdurl`. **57M → 44M (−13M)**, test PASS.

## Phase 6 — make jinja2/requests/watchdog/tqdm optional  ✅

None are loaded by `import dagster` or `materialize()` (verified). Moved to a new
`server` extra; uninstalled them + transitive deps (urllib3, certifi,
charset_normalizer, idna, MarkupSafe). **44M → 37M (−7M)**, test PASS.
(`universal_pathlib`/`fsspec` kept — they ARE used via `upath` during materialize.)

## Phase 4 — pytz → stdlib zoneinfo  ✅

`pytz` used in only 2 spots: vendored croniter (`pytz.utc`, a py2-only fallback —
py3 already uses `datetime.timezone.utc`) and `auto_materialize_rule.py`
(timezone-name validation → `zoneinfo.available_timezones()`). Removed pytz.
**37M → 35M (−2M)**, test PASS; cron scheduling + tz validation verified.

## Current standing

| Stage | site-packages | real-install equiv | vs 140M baseline |
|---|---|---|---|
| Brief baseline | — | 140M | — |
| Phase 3 (no sqlalchemy) | 57M | 63M | −55% |
| Phase 5 (no rich) | 44M | — | |
| Phase 6 (no jinja2/requests/…) | 37M | — | |
| Phase 4 (no pytz) | **35M** | **~41M** | **−71%** |

Real-install equivalent = third-party deps (21.7M) + dagster core source (18M) +
shared/pipes (1M) = ~41M = **29% of the original** (pip/ruff venv tooling excluded).

## Authoritative measurement — clean non-editable install

To measure exactly as the brief does (`du -sh site-packages/*`, which counts
dagster's copied core source), did a fresh **non-editable** install of the
slimmed packages into `.venv-measure`. Acceptance test PASSES on the clean install.

| | Size |
|---|---|
| TOTAL site-packages | 55.1 M |
| venv tooling (pip/setuptools — not dagster) | 12.4 M |
| **DAGSTER FOOTPRINT** | **42.8 M** |
| — dagster core pkgs (copied source) | 21.2 M |
| — pydantic + pydantic_core | 8.3 M |
| — tzdata | 2.6 M |
| — fsspec + upath (universal_pathlib) | 2.5 M |

**42.8M = 31% of the 140M baseline → 69% reduction**, with `materialize()`,
asset selection, and run/event/asset storage all working.

## Why ~70% is the practical floor (not 80%)

The 28M / 80% target is blocked by genuinely load-bearing pieces:
- **dagster core source ~20M** — `_core/definitions`, `execution`, `storage` are
  all on the materialize path; the deletable subsystems (alembic tree 0.7M, `_grpc`
  0.4M, `_daemon` 0.5M) are small AND back the optional `sql`/`grpc` extras, so
  deleting them would break those extras for ~1.6M of savings.
- **pydantic 8.3M** — the config/resource system; cannot be removed.
- **tzdata 2.6M** — needed by `zoneinfo` on platforms without a system tz db (Windows).
- **fsspec/upath 2.5M** — used via `UPath` during materialize for IO-manager paths.

Reaching 28M would require gutting core functionality or dropping pydantic —
neither compatible with "keep the public API working." The remaining levers
(replace UPath with stdlib pathlib for local FS, conditional tzdata) are
invasive/risky for ~5M.

## Final tally

| Approach | Lever | Saved |
|---|---|---|
| 1 | webserver/UI + graphql not installed | 42M |
| 3 | grpc/protobuf → optional, lazy | 39M |
| 3 | sqlalchemy/alembic/mako → stdlib sqlite3 | 21M |
| 3 | rich/pygments removed (unused) | 13M |
| 3 | jinja2/requests/watchdog/tqdm → optional | 7M |
| 3 | pytz → stdlib zoneinfo | 2M |
| 3 | antlr4 → hand-written parser | 1M |

**Original 140M → 42.8M = 69% reduction**, validated against the 3-asset
`materialize()` acceptance test at every step.

## Course compatibility check (dagster_essentials)

Verified the lightweight build runs the dagster_university `dagster_essentials`
course orchestration (`compact_tools/course_verification.py`, run in
`.venv-course`). DuckDB support restored via a tiny `dagster_duckdb` shim
(`compact_tools/dagster_duckdb_shim/`) — a `ConfigurableResource` over the stdlib
`duckdb` package providing `DuckDBResource.get_connection()`, since the original
`dagster-duckdb` integration was deleted in Phase 1.

- PART A — the REAL course modules (`resources`, `partitions`, `jobs`,
  `schedules`, `sensors`, `assets.trips`) all import and resolve: DuckDBResource,
  Monthly/Weekly partitions, 3 asset jobs, 2 schedules, the adhoc sensor.
- PART B — the REAL course `taxi_zones` + `taxi_trips` DuckDB assets execute
  end-to-end through a monthly-partitioned `define_asset_job` (sample local data;
  network download + geopandas/matplotlib viz assets skipped — pure course deps).
- Result: assets ✅, DuckDBResource ✅, partitions ✅, jobs ✅, schedule/sensor
  definitions ✅. Only auto-firing of schedules/sensors is unavailable (no daemon).

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
