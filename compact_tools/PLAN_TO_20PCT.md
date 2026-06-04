# Plan: get Dagster to 20% of baseline (~28M)

Baseline (brief): **140M**. Target: **≤28M** (80% reduction).
Current state: **78M** site-packages (44% reduction), acceptance test passing.

## Measurement caveats to fix first

- `pip` (12M) and `ruff` (0.45M, installed for linting) are **tooling, not
  dagster** — exclude them. A clean dagster-only number = ~65M today.
- We use an **editable** install, so dagster's own ~20M core source is NOT in
  site-packages. The brief's 140M counts it. For an apples-to-apples final
  number, do one **non-editable** install at the end and measure that.

## Dependency map (measured)

| Dep | Size | When loaded | Removal path |
|---|---|---|---|
| sqlalchemy | 18M | materialize() | Phase 3 — stdlib sqlite3 |
| pygments | 9.2M | materialize() (via rich) | Phase 5 — drop rich |
| pydantic + core | 8.3M | import | **KEEP** — config system, pervasive |
| rich | 2.9M | materialize() | Phase 5 — plain logging |
| pytz | 2.7M | import | Phase 4 — stdlib zoneinfo |
| tzdata | 2.6M | not loaded | Phase 4 — rely on system tz / keep small |
| alembic | 2.4M | materialize() | Phase 3 — drops with sqlalchemy |
| fsspec | 1.8M | materialize() (via upath) | Phase 6 — make universal_pathlib optional |
| jinja2 | 1.2M | not loaded | Phase 6 — make optional |
| urllib3+requests | 1.5M | not loaded | Phase 6 — make optional |
| mako | 0.75M | materialize() (via alembic) | Phase 3 — drops with alembic |
| markdown_it | 0.8M | materialize() (via rich) | Phase 5 — drops with rich |
| yaml, click, structlog, coloredlogs, etc. | ~4M | import | **KEEP** — small + core |

## Phases (each ends with acceptance test + measure.sh)

### Phase 3 — SQLAlchemy/alembic/mako → stdlib sqlite3   [~ -21M]  HARDEST
The only heavy deps still on the hot path. Not a deletion — a reimplementation.
1. Read the `RunStorage` / `EventLogStorage` ABCs
   (`_core/storage/runs/base.py`, `_core/storage/event_log/base.py`).
2. Implement `Sqlite3RunStorage` + `Sqlite3EventLogStorage` on the stdlib
   `sqlite3` module — only the methods the ephemeral/local instance calls.
3. Replace alembic migrations with a single versioned `CREATE TABLE` bootstrap
   + a tiny `schema_version` table for forward migrations.
4. Wire them into `create_ephemeral_instance()` / the default sqlite instance
   (`_core/instance/factory.py`, `_core/storage/sqlite_storage.py`).
5. Move `sqlalchemy`/`alembic` to an optional `sql` extra in `pyproject.toml`.
Risk: high (event log is ~3,500 lines; watch out for cursor/asset-key queries,
JSON serialization of event records, and run-status filtering).

### Phase 4 — pytz → stdlib zoneinfo   [~ -3M, up to -5M]
`pytz` is imported at startup. Replace usages with `zoneinfo` (stdlib, 3.9+).
Audit `grep -rn "import pytz\|pytz\."`. Keep `tzdata` only if a target platform
lacks the system tz database; otherwise drop it too. Make `pytz` optional.

### Phase 5 — drop rich/pygments/markdown_it   [~ -13M]
`rich` pulls `pygments` (9.2M) — the single biggest non-sql item. Used for
console logging + CLI formatting.
1. Replace `rich`-based log formatting with stdlib `logging` formatters.
2. Replace `rich` CLI tables/output with `tabulate` (already a dep) or plain text.
3. Audit `grep -rn "import rich\|from rich"`; make `rich` optional.
Risk: medium — many call sites, but all cosmetic (no execution logic).

### Phase 6 — make unused deps optional   [~ -4.5M]
None of these load during import or materialize():
- `universal_pathlib`/`fsspec` (2.5M) → optional `remote-io` extra
- `requests`/`urllib3` (1.5M) → optional (telemetry/HTTP) extra
- `jinja2` (1.2M) → optional
Guard their import sites lazily; move to extras in `pyproject.toml`.

### Phase 7 — trim dagster core source + final clean install   [~ -5–8M]
1. Delete distributed/remote-only subsystems unused for local materialize:
   `_daemon/`, `_grpc/`, scheduler/sensor/backfill, remote api
   (`_api/`, `_core/remote_representation/` grpc paths), step-delegating
   executor + non-default run launchers.
2. Remove the alembic migration tree (`_core/storage/alembic/`, ~100 files).
3. Uninstall `pip`-less measurement: do a fresh **non-editable** install of the
   trimmed core into a clean venv and run `measure.sh` for the headline number.

## Projected footprint

| After phase | site-packages (dagster-only, non-editable) |
|---|---|
| now | ~65M (+20M core source not yet counted) |
| Phase 3 (-21M) | ~44M |
| Phase 4 (-3M) | ~41M |
| Phase 5 (-13M) | ~28M |
| Phase 6 (-4.5M) | ~24M |
| Phase 7 (core trim) | **~20–24M** ✅ ≤28M target |

Order by value/risk: **3 → 5 → 4 → 6 → 7**. Phase 3 unblocks the most size and
is prerequisite for a clean story; Phase 5 is the next biggest single win.

## Hard constraints / keep-list
- `pydantic` (8.3M) stays — it underpins the config/resource system everywhere.
  This sets a practical floor; the 28M target is only reachable *with* pydantic
  present, which is why core-source trimming (Phase 7) is required to close the gap.
- Run `compact_tools/acceptance_test.py` after every sub-step; never batch.
