# Merged lite engine — best-of-both decisions

Branch `lite-engine-merged` combines `local_conversion` (partner) and
`lite-engine-extraction` (mine). Both fork from `7c85e3bd52`. Rule applied:
**keep whichever did each thing better; on a tie, keep the smaller one that
still preserves function.**

| Concern | Winner | Why |
|---|---|---|
| Dependency removal mechanism | **Partner** | Optional extras (`server`/`sql`/`grpc`/`remote-io`) are reversible & upstream-friendly vs. hard deletion |
| Run / event-log storage | **Partner** | stdlib `sqlite3` storage is persistent across runs (mine was in-memory dict, no persistence); both use zero external deps |
| `antlr4` | **Partner** | Hand-written recursive-descent asset-selection parser (48/48 validated) removes the dep entirely; mine kept the 0.58 MB dep |
| `pytz` → `zoneinfo` | **Partner** | stdlib swap drops pytz (~2.7 MB); I had skipped it |
| Non-core monorepo packages | **Partner** | Deleted all integration libs / graphql / cloud / webserver source (repo-size win, no effect on core engine) |
| `pywin32` (~15.8 MB) | **Mine** | Never imported on the in-process path → moved to `server` extra |
| `universal_pathlib` + `fsspec` (~2.5 MB) | **Mine** | Default IO manager falls back to stdlib `pathlib.Path` for local FS (`_core/storage/_upath_compat.py`) → moved to `remote-io` extra |
| `rich`/`pygments`, `grpc`, `sqlalchemy` | tie | Both removed; identical outcome |
| Verification | **Both kept** | Partner's `compact_tools/` (real Dagster-University taxi course) + mine `lite_extraction/` (smoke, 10 essentials, tree-shaken bundle) |

## Net effect

The merged default dependency set is the **leanest of the three branches** — it
applies the partner's removals *and* mine. No `grpc`, `sqlalchemy`, `pytz`,
`antlr4`, `rich`/`pygments`, `pywin32`, `universal_pathlib`/`fsspec`,
`jinja2`/`requests`/`watchdog`/`tqdm` in the default install. Everything is
restorable via extras: `dagster[sql]`, `dagster[grpc]`, `dagster[server]`,
`dagster[remote-io]`.

Footprint (this venv, editable, `__pycache__` stripped): site-packages 16.7 MB
+ dagster core source 9.6 MB = **26.3 MB**. Remaining weight is load-bearing:
pydantic/pydantic_core (8.5 MB), tzdata (1.7 MB, zoneinfo data), and the core
engine source.

## Validation (all green, with the combined removals applied)

- Partner's `compact_tools/acceptance_test.py` → PASS
- `lite_extraction/smoke_test.py` → GREEN
- `lite_extraction/essentials_test.py` → 10/10, including string `"*"` asset
  selection running through the **hand-written parser with antlr4 uninstalled**,
  and IO-manager round-trips through the **pathlib fallback with upath/fsspec
  uninstalled** — the two riskiest deltas, both confirmed functional.
- Partner's full taxi-course verification was run on their machine
  (`compact_tools/course_verification.py`); it is not reproducible here (hardcoded
  course-source path + geopandas/matplotlib), but the IO-manager path it relies
  on is exercised by the passing acceptance + essentials tests.
