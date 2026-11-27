---
title: dbt project on Snowflake component
sidebar_position: 350
description: Orchestrate a dbt project running natively on Snowflake with Dagster
tags: [dagster-supported, etl, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-snowflake
pypi: https://pypi.org/project/dagster-snowflake/
sidebar_custom_props:
  logo: images/integrations/snowflake.svg
partnerlink: https://www.snowflake.com/en/
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

The `SnowflakeDbtProjectComponent` orchestrates a dbt project that runs **natively on Snowflake**
(the [dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake)
feature) and exposes it to Dagster as a set of assets.

Unlike the [`dagster_dbt.DbtProjectComponent`](/integrations/libraries/dbt), which runs `dbt`
locally, this component never executes dbt on the Dagster host. It is modeled on the
[dbt Cloud component](/integrations/libraries/dbt/dbt-cloud): there is **no local copy of the dbt
project**, and execution happens remotely inside Snowflake's managed runtime via
`EXECUTE DBT PROJECT`. Dagster fetches the dbt manifest from Snowflake, builds the asset graph from
it, and submits, polls, and reports each run.

## Prerequisites

1. The dbt project is already deployed to Snowflake as a `DBT PROJECT` object (via
   `CREATE DBT PROJECT …` or `snow dbt deploy`). The component does not upload or create the
   project object.
2. Install `dagster-snowflake` with the optional `dbt` extra:

   ```bash
   pip install 'dagster-snowflake[dbt]'
   ```

3. A **non-interactive** Snowflake credential. Key-pair authentication is strongly recommended (it
   is exempt from MFA and works headless). Do **not** use `authenticator: externalbrowser` (SSO) —
   it cannot complete from a Dagster run.

## Configuration

Add the component to a `defs.yaml` file in your Dagster project:

```yaml
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
  include_metadata: [row_count, column_metadata] # optional
```

## How it works

- **Asset graph (state refresh).** The component fetches the dbt manifest _from Snowflake_: it
  probes the account for `SYSTEM$LOCATE_DBT_ARTIFACTS` (failing cleanly if the feature isn't
  available), runs `EXECUTE DBT PROJECT … ARGS='parse'`, locates the artifacts with
  `SYSTEM$LOCATE_DBT_ARTIFACTS(<query_id>)`, downloads `manifest.json`, and caches it as the
  component's defs-state. No dbt artifacts are committed to your repository. Use
  `manifest_args: [compile]` if your project needs compilation to parse.
- **Execution (async + cancellable).** `EXECUTE DBT PROJECT … ARGS='build …'` is submitted
  asynchronously and polled to completion (interval controlled by `poll_interval_seconds`). If the
  Dagster run is interrupted, the component issues `SYSTEM$CANCEL_QUERY(<query_id>)` so the
  Snowflake query is spun down rather than left orphaned. The dbt log is fetched via
  `SYSTEM$GET_DBT_LOG` and surfaced in the Dagster compute logs. Each run's session is tagged with a
  `QUERY_TAG` containing the Dagster run id, so Snowflake credit usage is attributed back to the
  originating Dagster run.
- **Materializations & metadata.** After the run, `run_results.json` is downloaded and translated
  into `MaterializeResult`s and `AssetCheckResult`s with metadata at parity with the dbt core and
  dbt Cloud components.

## Subsetting

The generated assets support `can_subset=True`. When Dagster launches a subset, the component builds
a `--select`ed `EXECUTE DBT PROJECT` statement covering exactly the selected models and checks, using
the same selection logic as the dbt core and dbt Cloud components.

## Optional metadata

`include_metadata` is off by default (matching dbt core). Both addons are fetched in **bulk from
`INFORMATION_SCHEMA`** after the run — at most one query per database, served from cloud services
(no warehouse) — instead of one query per model:

- `row_count` → `INFORMATION_SCHEMA.TABLES.ROW_COUNT` per materialized model (views are skipped).
- `column_metadata` → column schema from `INFORMATION_SCHEMA.COLUMNS` plus column-level lineage
  derived from the run's compiled SQL.

:::note
`INFORMATION_SCHEMA.TABLES.ROW_COUNT` is maintained by Snowflake and can be slightly eventually
consistent; in exchange it avoids re-scanning every table with `SELECT count(*)`.
:::

## Observation mode

Set `create_sensor: true` to add a polling sensor that reports dbt runs executed in Snowflake
**outside** Dagster (Snowflake Tasks, Snowsight, `snow dbt execute`). It polls
`DBT_PROJECT_EXECUTION_HISTORY`, downloads each new run's `run_results.json`, and emits
`AssetMaterialization`s.

Dagster-triggered runs are de-duplicated using the session `QUERY_TAG` marker (looked up via
`INFORMATION_SCHEMA.QUERY_HISTORY`), so Dagster-materialized and externally-triggered runs coexist
without double-reporting.

## Refreshing the asset graph

The asset graph is derived from the manifest cached as the component's defs-state. If the project is
redeployed to Snowflake out-of-band, refresh the cached manifest with:

```bash
dg utils refresh-defs-state
```

In local development the state is refreshed automatically.

## Customization

Subclass and override `get_asset_spec` (asset keys, metadata, kinds), `execute` (run behavior), or
supply a `translation` function in YAML — the same extension points as the other dbt components.
