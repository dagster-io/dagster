---
title: 'Observe Airflow tasks'
sidebar_position: 300
---

In the previous step, "[Peer the Airflow instance with a Dagster code location](/guides/migrate/airflow-to-dagster/task-level-migration/peer)", we connected the example Airflow instance to a Dagster code location.

The next step is to represent the Airflow workflows more richly by observing the data assets that are produced by the Airflow tasks. Similar to the peering step, this step does not require any changes to Airflow code.

## Create asset specs for Airflow tasks

In order to observe the assets produced by the Airflow tasks in this tutorial, you will need to define the relevant assets in the Dagster code location.

In this example, there are three sequential tasks:

1. `load_raw_customers` loads a CSV file of raw customer data into duckdb.
2. `build_dbt_models` builds a series of dbt models (from [jaffle shop](https://github.com/dbt-labs/jaffle_shop_duckdb)) combining customer, order, and payment data.
3. `export_customers` exports a CSV representation of the final customer file from duckdb to disk.

First, you will need to create a set of <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> that correspond to the assets produced by these tasks. Next, you will annotate these asset specs so Dagster can associate them with the Airflow tasks that produce them.

The first and third tasks involve a single table each, so we will manually construct asset specs for these two tasks. We will use the <PyObject section="libraries" module="dagster_airlift" object="core.assets_with_task_mappings" displayText="assets_with_task_mappings" /> function in the `dagster-airlift` package to annotate these asset specs with the tasks that produce them. Assets which are properly annotated will be materialized by the Airlift sensor once the corresponding task completes, and these annotated specs are then provided to the `defs` argument to <PyObject section="libraries" module="dagster_airlift" object="core.build_defs_from_airflow_instance" displayText="defs_from_airflow_instance" />.

The second task, `build_dbt_models`, will require building a set of `dbt` asset definitions. We will use the <PyObject section="libraries" module="dagster_dbt" object="dbt_assets" decorator /> decorator from the [`dagster-dbt`](https://docs.dagster.io/api/python-api/libraries/dagster-dbt) package to generate these definitions using Dagster's dbt integration.

First, install the `dbt` extra of `dagster-airlift`:

```bash
uv pip install 'dagster-airlift[dbt]'
```

Next, construct the assets:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe.py" language="python" />

## View observed assets

Once you have created the three assets above, you should be able to navigate to the UI, reload your Dagster definitions, and see a full representation of the `dbt` project and other data assets in your code:

<img src="/images/integrations/airlift/observe.svg" alt="Observed asset graph in Dagster" />

After you initiate a run of the DAG in Airflow, you should see the newly created assets materialize in Dagster as each task completes.

:::info

There will be a delay between when tasks complete in Airflow and assets materialize in Dagster, managed by the Dagster sensor. This sensor runs every 30 seconds by default, but you can change this interval using the `minimum_interval_seconds` argument to <PyObject section="schedules-sensors" module="dagster" object="sensor" />, down to a minimum of one second.

:::

## Update the asset check to the `customers_csv` asset

Now that we've introduced an asset explicitly for the `customers.csv` file output by the DAG, we should update the asset check constructed during the peering step to point to the `customers_csv` asset. To do this, change the `asset` targeted by the `@asset_check` decorator to `AssetKey(["customers_csv"])`. Updating this asset check ensures that even when the DAG is deleted, the asset check will live on:

<CodeExample
  path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe_check_on_asset.py"
  language="python"
  startAfter="asset-check-update-start"
  endBefore="asset-check-update-end"
/>

To see what the full code should look like after the asset check, see the [example code in GitHub](https://github.com/dagster-io/dagster/tree/master/examples/airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe_check_on_asset.py).

## Add partitions

If your Airflow tasks produce time-partitioned assets, Airlift can automatically associate your materializations to the relevant partitions. In this example, in the `rebuild_customers_list` asset, data is partitioned daily in each created table, and the Airflow DAG runs on a `@daily` cron schedule. We can likewise add a `DailyPartitionsDefinition` to each of our assets:

<CodeExample
  path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe_with_partitions.py"
  language="python"
/>

Now, every time the sensor triggers a materialization for an asset, it will automatically have a partition associated with it.

You can try this out by kicking off an Airflow backfill for today:

```bash
airflow dags backfill rebuild_customers_list --start-date $(date +"%Y-%m-%d")
```

After this DAG run completes, you should see a partitioned materialization appear in Dagster:

![Partitioned materialization in Dagster](/images/integrations/airlift/partitioned_mat.png)

Finally, run `airflow db clean` to delete Airflow runs so you can initiate this backfill again for testing in the future:

```bash
airflow db clean
```

:::note

In order for partitioned assets to work with `dagster-airlift`, the following things need to be true:

- The asset can only be time-window partitioned. This means static, dynamic, and multi partitioned definitions will require custom functionality.
- The partitioning scheme must match up with the [logical_date/execution_date](https://airflow.apache.org/docs/apache-airflow/stable/faq.html#what-does-execution-date-mean) of corresponding Airflow runs. That is, each logical*date should correspond \_exactly* to a partition in Dagster.

:::

## Next steps

In the next step, "[Migrate Airflow tasks](/guides/migrate/airflow-to-dagster/task-level-migration/migrate)", we will migrate Airflow DAG code to Dagster.
