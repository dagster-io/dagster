# SnowflakeDbtProjectComponent

Run a dbt project **natively on Snowflake** (the
[dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake)
feature) and expose it to Dagster as a set of assets.

Unlike `dagster_dbt.DbtProjectComponent` (which runs `dbt` locally) this component never executes
dbt on the host. It is modeled on `dagster_dbt.DbtCloudComponent`: there is **no local copy of the
dbt project**, and execution happens remotely — here, inside Snowflake's managed runtime via
`EXECUTE DBT PROJECT`.

> **Preview.** This component is in preview and may change in patch releases.

## Prerequisites

1. The dbt project is already deployed to Snowflake as a `DBT PROJECT` object
   (`CREATE DBT PROJECT …` / `snow dbt deploy`).
2. Install the optional dbt extra:

   ```bash
   pip install 'dagster-snowflake[dbt]'
   ```

3. A **non-interactive** Snowflake credential. Key-pair auth is strongly recommended (it is exempt
   from MFA and works headless). Do **not** use `authenticator: externalbrowser` (SSO) — it can't
   complete from a Dagster run and fails with a SAML error.

## Quickstart

```yaml
# defs.yaml
type: dagster_snowflake.SnowflakeDbtProjectComponent
attributes:
  snowflake_dbt_project_name: "analytics.dbt.jaffle_shop" # database.schema.project
  snowflake:
    account: "{{ env.SNOWFLAKE_ACCOUNT }}"
    user: "{{ env.SNOWFLAKE_USER }}"
    private_key_path: "{{ env.SNOWFLAKE_PRIVATE_KEY_PATH }}"
    private_key_password: "{{ env.SNOWFLAKE_PRIVATE_KEY_PASSPHRASE }}" # omit if key is unencrypted
    role: TRANSFORMER
    warehouse: TRANSFORMING
    database: ANALYTICS
    schema: DBT
  cli_args: [build]
  include_metadata: [row_count, column_metadata] # optional, see below
```

## How it works

- **Asset graph (state refresh).** The component fetches the dbt manifest _from Snowflake_: it runs
  `EXECUTE DBT PROJECT … ARGS='parse'`, locates the artifacts with
  `SYSTEM$LOCATE_DBT_ARTIFACTS(<query_id>)`, downloads `manifest.json`, and caches it as the
  component's defs-state. No dbt artifacts are committed to your repo. (Use `manifest_args: [compile]`
  if your project needs compilation to parse.)
- **Execution.** `EXECUTE DBT PROJECT … ARGS='build …'` runs over the `SnowflakeResource`
  connection. This is **synchronous** — the statement blocks until the dbt run finishes (there is no
  intermediate streaming). The dbt log is then fetched via `SYSTEM$GET_DBT_LOG` and surfaced in the
  Dagster logs.
- **Materializations & metadata.** After the run, `run_results.json` is downloaded and translated
  into `MaterializeResult`s / `AssetCheckResult`s with metadata at parity with the dbt core and dbt
  Cloud components (`unique_id`, `invocation_id`, `execution_duration`, completed-at timestamp, test
  status), plus the static dbt metadata carried on each `AssetSpec`.

## Subsetting

`can_subset=True`. When Dagster launches a subset, the component builds a `--select`ed
`EXECUTE DBT PROJECT` statement covering exactly the selected models/checks, using the same
selection logic (`get_subset_selection_for_context`) as the dbt core and dbt Cloud components.

## Optional metadata (`include_metadata`)

Off by default (matching dbt core). Each addon runs extra warehouse queries per model after the run:

- `row_count` → `SELECT count(*)` per materialized model (views skipped) → `dagster/row_count`.
- `column_metadata` → column schema via `DESCRIBE TABLE` plus column-level lineage (derived from the
  run's compiled SQL, extracted from `dbt_artifacts.zip`) → `dagster/column_schema`,
  `dagster/column_lineage`.

## Observation mode (`create_sensor`)

Set `create_sensor: true` to add a polling sensor that reports dbt runs executed in Snowflake
**outside** Dagster (Snowflake Tasks, Snowsight, `snow dbt execute`). It polls
`DBT_PROJECT_EXECUTION_HISTORY`, downloads each new run's `run_results.json`, and emits
`AssetMaterialization`s — analogous to the dbt Cloud component's external-run sensor.

**De-duplication.** Like dbt Cloud (which filters its dedicated adhoc-job runs), Dagster-triggered
runs are skipped: while the sensor is enabled, `execute()` tags its invocations with a sentinel dbt
var that appears in the history's `ARGS` column, and the sensor filters those out. So
Dagster-materialized and externally-triggered runs can coexist without double-reporting.

## Customization

Subclass and override `get_asset_spec` (asset keys/metadata/kinds), `execute` (run behavior), or the
translation function in YAML — the same extension points as the other dbt components.

## Caveats

- Preview feature; assumes the `DBT PROJECT` object is already deployed (the component does not
  `CREATE OR REPLACE`/upload it).
- Per-model metadata fetching is sequential (dbt core parallelizes it); fine for typical projects.
- Observation-mode de-dup relies on the `ARGS` column reflecting the injected marker; if it doesn't,
  the worst case is double-reporting (never a crash). Marker injection only happens when
  `create_sensor` is enabled.
