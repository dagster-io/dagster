---
title: dbt patterns and best practices
description: Best practices and advanced patterns for dbt.
sidebar_position: 250
---

This guide covers advanced patterns and best practices for integrating dbt with Dagster, helping you build more maintainable data pipelines.

## Preventing concurrent dbt snapshots

[dbt snapshots](https://docs.getdbt.com/docs/build/snapshots) track changes to data over time by comparing current data to previous snapshots. Running snapshots concurrently can corrupt these tables, so it's critical to ensure only one snapshot operation runs at a time.

### Option 1: Separate snapshots from other models

Create separate dbt component definitions to isolate snapshots from your regular dbt models. First, scaffold two dbt components:

```bash
# Create component for regular models
dg scaffold defs dagster_dbt.DbtProjectComponent dbt_models

# Create component for snapshots
dg scaffold defs dagster_dbt.DbtProjectComponent dbt_snapshots
```

Configure the regular models component to exclude snapshots:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/models.yaml"
  title="my_project/defs/dbt_models/defs.yaml"
  language="yaml"
/>

Configure the snapshots component with concurrency control:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/snapshot.yaml"
  title="my_project/defs/dbt_snapshots/defs.yaml"
  language="yaml"
/>

### Option 2: Configure concurrency pools

Configure your Dagster instance to create pools with maximum concurrency of 1. Add this configuration to your `dagster.yaml` (for Dagster Open Source) or deployment settings (for Dagster+):

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/dagster.yaml"
  title="dagster.yaml"
  language="yaml"
/>

Then set the pool limit for the snapshot pool:

```bash
# Set pool limit using CLI
dagster instance concurrency set dbt-snapshots 1
```

### Option 3: Manage multiple snapshot groups with Dagster components

For large projects with many snapshots, you can create multiple snapshot groups while still preventing concurrency issues within each group. Create separate [Dagster components](/guides/build/components/creating-new-components/creating-and-registering-a-component) for different business domains:

```bash
# Create component for sales snapshots
dg scaffold defs dagster_dbt.DbtProjectComponent dbt_snapshots_sales

# Create component for inventory snapshots
dg scaffold defs dagster_dbt.DbtProjectComponent dbt_snapshots_inventory
```

Sales snapshots component:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/snapshot_sales.yaml"
  title="my_project/defs/dbt_snapshots_sales/defs.yaml"
  language="yaml"
/>

Inventory snapshots component:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/snapshot/snapshot_inventory.yaml"
  title="my_project/defs/dbt_snapshots_inventory/defs.yaml"
  language="yaml"
/>

Configure separate [pool limits for each domain](/guides/operate/managing-concurrency/concurrency-pools#limit-the-number-of-assets-or-ops-actively-executing-across-all-runs). This approach allows snapshots from different business domains to run in parallel while preventing concurrent execution within each domain, reducing the risk of corruption while maintaining reasonable performance.

## Microbatch incremental models

dbt's [microbatch incremental strategy](https://docs.getdbt.com/docs/build/incremental-microbatch) uses a fundamentally different batching model than regular incremental models. Understanding the difference determines which CLI flags you pass from Dagster.

### Regular incremental models

With regular incremental models, **you** control the row filtering. Dagster passes `--vars` to provide date boundaries, and your SQL uses `{% if is_incremental() %}` to filter rows within those boundaries. dbt runs the model once for the entire window:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets_incrementals.py"
  startAfter="start_incremental_dbt_models"
  endBefore="end_incremental_dbt_models"
  title="dbt_assets.py"
/>

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/incremental_model.sql"
  title="models/incremental_model.sql"
  language="sql"
/>

### Microbatch incremental models

With microbatch, **dbt** controls the batching. You configure the model with an `event_time` column and a `batch_size`, and dbt's engine automatically subdivides the window into discrete batches — running the model once per batch. Your SQL doesn't need a manual filter; dbt injects it based on `event_time`.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/microbatch_model.sql"
  title="models/microbatch_model.sql"
  language="sql"
/>

Dagster passes `--event-time-start` and `--event-time-end` to tell the microbatch engine which window to process. These flags drive the engine directly. Passing `--vars` instead has no effect on batch scheduling — it only injects values into the SQL template — which is why misconfigured microbatch models silently process all batches from `begin` to now rather than the intended partition window.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets_microbatch_incrementals.py"
  startAfter="start_microbatch_dbt_models"
  endBefore="end_microbatch_dbt_models"
  title="dbt_assets.py"
/>

Because dbt processes one `batch_size` interval at a time, your `PartitionsDefinition` should match:

| dbt `batch_size` | Dagster `PartitionsDefinition` |
| ---------------- | ------------------------------ |
| `day`            | `DailyPartitionsDefinition`    |
| `month`          | `MonthlyPartitionsDefinition`  |
| `year`           | `YearlyPartitionsDefinition`   |

The `start_date` of the `PartitionsDefinition` should match the model's `begin` config so Dagster backfills align with dbt's batch history.

## Organizing dbt assets into groups

By default, all dbt assets land in a single `dbt` group. To split them into meaningful groups, subclass <PyObject section="libraries" integration="dbt" module="dagster_dbt" object="DagsterDbtTranslator" /> and override `get_group_name`. Common grouping strategies:

- **Model directory** (e.g., `marts/`, `staging/`, `intermediate/`) for layer-based pipelines.
- **dbt tags** (e.g., `finance`, `marketing`) when you already use tags to organize models.
- **`meta` configuration** for explicit per-model overrides defined in dbt source control.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_patterns_extras.py"
  startAfter="start_grouping_translator"
  endBefore="end_grouping_translator"
  title="src/<project_name>/defs/dbt_assets.py"
/>

Pick one strategy or combine them; any model that doesn't match the rules falls back to the default group returned at the end.

## Running tagged dbt tests

dbt tests are not Dagster assets. They are operations that run against assets, so `build_dbt_asset_selection` with a tag filters the _assets_ that have that tag, not the tests.

To run only the tests with a specific tag (including source tests), invoke the dbt CLI directly through <PyObject section="libraries" integration="dbt" module="dagster_dbt" object="DbtCliResource" /> and use dbt's selection syntax:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_patterns_extras.py"
  startAfter="start_tagged_tests"
  endBefore="end_tagged_tests"
  title="src/<project_name>/defs/dbt_tests.py"
/>

The asset-based approach using `build_dbt_asset_selection` with tags is the right tool for selecting _models_, but it cannot select tests on sources or untagged tests on tagged models. Use the CLI pattern above when test selection is what you need.

## Running specific dbt models from the UI

To materialize a specific subset of dbt models on demand, navigate to your code location's **Assets** tab and use the asset selection input. The input accepts dbt selection syntax similar to `dbt -s`:

- Model names directly: `model1 model2`
- dbt selection syntax: `tag:staging`, `+model`, `model+`
- Filter by group, tag, or asset key

This is the typical path for ad-hoc runs (recovering from outages, materializing a small set of new models) without writing a custom job.

## Macro changes are not detected by `code_version_changed`

`AutomationCondition.code_version_changed()` does not detect changes to dbt macros. Code versions for dbt assets are derived from each model's `raw_code` or `raw_sql` in the `manifest.json`. Macros and ephemeral models are not imported into the Dagster asset graph, so their content is not part of the code version calculation.

If you change a macro that downstream models depend on, the consuming models' code versions do not change, and the automation condition will not mark them stale. Until [dagster#22566](https://github.com/dagster-io/dagster/issues/22566) is resolved, treat macro changes as a manual trigger:

- Identify which models depend on the changed macros.
- Manually materialize those assets after deploying the macro change.
- For workflows where this happens often, consider a custom automation condition that watches macro file modifications, or fall back to a time-based trigger.

## Recovering from snapshot SQL compilation errors after package updates

dbt snapshots can start failing across all environments simultaneously after a `dbt deps` update if a transitive package changes a macro that snapshot-related models compile against. Symptoms include syntax errors at column positions that look unrelated to your code (for example, `syntax error line 15 at position 21 unexpected ')'` from Snowflake) and local environments working until packages are reinstalled.

Reset the dbt environment to clear cached dependencies:

```shell
dbt clean && dbt deps
```

Then re-run the snapshots. To prevent recurrence, pin package versions in `packages.yml` rather than letting them float, and test snapshots in a development environment after any package upgrade before promoting to production.

## Recovering from infrastructure interruptions

To gracefully recover from infrastructure interruptions, such as a Kubernetes node eviction or a pod termination, use the `FROM_ASSET_FAILURE` run retry strategy with a `dagster/retry_on_asset_or_op_failure` setting value of `false` to use persisted asset materialization records from the event log and automatically exclude already-materialized assets during retry. This enables recovering without requiring persisted dbt artifacts. See [Configuring run retries](/deployment/execution/run-retries).

<CodeExample
  path="docs_snippets/docs_snippets/deployment/execution/asset_job_from_asset_failure_retries.py"
  startAfter="start_from_asset_failure_job"
  endBefore="end_from_asset_failure_job"
  title="src/my_project/jobs.py"
/>
