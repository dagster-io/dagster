---
title: Snowflake dbt Project component
sidebar_position: 350
description: Run a dbt project natively on Snowflake (dbt Projects on Snowflake) and expose it to Dagster as assets.
tags: [dagster-supported, etl, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-snowflake
pypi: https://pypi.org/project/dagster-snowflake/
sidebar_custom_props:
  logo: images/integrations/snowflake.svg
partnerlink: https://www.snowflake.com/en/
---

The `dagster-snowflake` library provides a `SnowflakeDbtProjectComponent` that runs a dbt project
**natively on Snowflake** — using the
[dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake)
feature — and exposes it to Dagster as a set of assets.

:::info Preview

`SnowflakeDbtProjectComponent` is in preview and may change in patch releases.

:::

## How it compares to the other dbt components

| Component                                                    | Where dbt runs                                           | Project source                               |
| ------------------------------------------------------------ | -------------------------------------------------------- | -------------------------------------------- |
| [`DbtProjectComponent`](/integrations/libraries/dbt)         | Locally, via the `dbt` CLI                               | A local dbt project                          |
| [`DbtCloudComponent`](/integrations/libraries/dbt/dbt-cloud) | Remotely, in dbt Cloud                                   | dbt Cloud workspace                          |
| **`SnowflakeDbtProjectComponent`**                           | Remotely, **inside Snowflake** via `EXECUTE DBT PROJECT` | A `DBT PROJECT` object deployed to Snowflake |

Like `DbtCloudComponent`, there is **no local copy of the dbt project**: the manifest is fetched from
Snowflake and execution happens remotely. It is a
[state-backed component](/guides/build/components/state-backed-components) — the fetched manifest is
cached as component state, so no dbt artifacts are committed to your repository.

## Prerequisites

1. The dbt project is already deployed to Snowflake as a `DBT PROJECT` object (via
   `CREATE DBT PROJECT …` or `snow dbt deploy`).
2. Install the optional dbt extra:

   <PackageInstallInstructions packageName="'dagster-snowflake[dbt]'" />

3. A **non-interactive** Snowflake credential. Key-pair authentication is strongly recommended — it
   is exempt from MFA and works headless. Do **not** use `authenticator: externalbrowser` (SSO); it
   cannot complete from a Dagster run and fails with a SAML error.

## Example

```yaml title="my_project/defs/snowflake_dbt/defs.yaml"
type: dagster_snowflake.SnowflakeDbtProjectComponent
attributes:
  snowflake_dbt_project_name: 'analytics.dbt.jaffle_shop' # database.schema.project
  snowflake:
    account: '{{ env.SNOWFLAKE_ACCOUNT }}'
    user: '{{ env.SNOWFLAKE_USER }}'
    private_key_path: '{{ env.SNOWFLAKE_PRIVATE_KEY_PATH }}'
    private_key_password: '{{ env.SNOWFLAKE_PRIVATE_KEY_PASSPHRASE }}' # omit if key is unencrypted
    role: TRANSFORMER
    warehouse: TRANSFORMING
    database: ANALYTICS
    schema: DBT
  cli_args: [build]
  include_metadata: [row_count, column_metadata] # optional; see below
```

## How it works

- **Asset graph (state refresh).** The component fetches the dbt manifest from Snowflake: it runs
  `EXECUTE DBT PROJECT … ARGS='parse'`, locates the artifacts with
  `SYSTEM$LOCATE_DBT_ARTIFACTS`, downloads `manifest.json`, and caches it as component state. Set
  `manifest_args: [compile]` if your project must be compiled to produce a manifest.
- **Execution.** `EXECUTE DBT PROJECT … ARGS='build …'` runs over the Snowflake connection. This is
  **synchronous** — the statement blocks until the dbt run finishes (there is no intermediate
  streaming). The dbt log is then fetched with `SYSTEM$GET_DBT_LOG` and written to the run's compute
  (stdout) logs.
- **Materializations and metadata.** After the run, `run_results.json` is translated into
  materializations and asset check results with metadata at parity with the dbt core and dbt Cloud
  components (`unique_id`, `invocation_id`, execution duration, completed-at timestamp, test status),
  plus the static dbt metadata carried on each asset.

## Subsetting

When you materialize a subset of the assets, the component runs a `--select`ed `EXECUTE DBT PROJECT`
statement covering exactly the selected models and checks, using the same selection logic as the dbt
core and dbt Cloud components.

## Optional metadata

The `include_metadata` option is off by default (matching the dbt core component). Each addon issues
extra warehouse queries per model after the run:

- `row_count` — `SELECT count(*)` per materialized model (views are skipped) → `dagster/row_count`.
- `column_metadata` — column schema via `DESCRIBE TABLE` plus column-level lineage derived from the
  run's compiled SQL → `dagster/column_schema` and `dagster/column_lineage`.

## Observing externally-triggered runs

Set `create_sensor: true` to add a polling sensor that reports dbt runs executed in Snowflake
**outside** Dagster (Snowflake Tasks, Snowsight, or `snow dbt execute`). The sensor polls
`DBT_PROJECT_EXECUTION_HISTORY` and emits materializations from each new run's `run_results.json`,
analogous to the dbt Cloud component's external-run sensor. Runs that Dagster itself triggered are
tagged and filtered out, so Dagster-materialized and externally-triggered runs can coexist without
double-reporting.

## Customization

As with the other dbt components, you can subclass `SnowflakeDbtProjectComponent` and override
`get_asset_spec` (asset keys, metadata, kinds) or `execute` (run behavior), or apply a `translation`
function in YAML.

## Caveats

- Preview feature; the component assumes the `DBT PROJECT` object is already deployed (it does not
  create or upload it).
- Per-model `include_metadata` queries run sequentially.
- The observation sensor's de-duplication relies on the dbt run's `ARGS` reflecting the injected
  marker; in the worst case it double-reports rather than failing.
