---
title: "Observe assets"
sidebar_position: 300
---

Previously, we completed the ["Peering" stage](peer) of the Airflow migration process by peering the Airflow instance with a Dagster code location.

The next step is to represent our Airflow workflows more richly by observing the data assets that are produced by our tasks. Similar to the peering step, this stage does not require _any changes_ to Airflow code.

In order to do this, we must define the relevant assets in the Dagster code location.

In our example, we have three sequential tasks:

1. `load_raw_customers` loads a CSV file of raw customer data into duckdb.
2. `run_dbt_model` builds a series of dbt models (from [jaffle shop](https://github.com/dbt-labs/jaffle_shop_duckdb)) combining customer, order, and payment data.
3. `export_customers` exports a CSV representation of the final customer file from duckdb to disk.

We will first create a set of asset specs that correspond to the assets produced by these tasks. We will then annotate these asset specs so that Dagster can associate them with the Airflow tasks that produce them.

The first and third tasks involve a single table each. We can manually construct specs for these two tasks. Dagster provides the `assets_with_task_mappings` utility to annotate our asset specs with the tasks that produce them. Assets which are properly annotated will be materialized by the Airlift sensor once the corresponding task completes: These annotated specs are then provided to the `defs` argument to `build_defs_from_airflow_instance`.

We will also create a set of dbt asset definitions for the `build_dbt_models` task. We can use the `dagster-dbt`-supplied decorator `@dbt_assets` to generate these definitions using Dagster's dbt integration.

First, you need to install the extra that has the dbt factory:

```bash
uv pip install 'dagster-airlift[dbt]'
```

Then, we will construct our assets:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe.py" language="python"/>

### Viewing observed assets

Once your assets are set up, you should be able to reload your Dagster definitions and see a full representation of the dbt project and other data assets in your code.

<img
  src="/images/integrations/airlift/observe.svg"
  alt="Observed asset graph in Dagster"
/>

Kicking off a run of the DAG in Airflow, you should see the newly created assets materialize in Dagster as each task completes.

_Note: There will be some delay between task completion and assets materializing in Dagster, managed by the sensor. This sensor runs every 30 seconds by default (you can reduce down to one second via the `minimum_interval_seconds` argument to `sensor`)._

### Moving the asset check

Now that we've introduced an asset explicitly for the `customers.csv` file output by the DAG, we should move the asset check constructed during the Peering step to instead be on the `customers_csv` asset. Simply change the `asset` targeted by the `@asset_check` decorator to be `AssetKey(["customers_csv"])`. Doing this ensures that even when we delete the DAG, the asset check will live on.

When done, our code will look like this.

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe_check_on_asset.py" language="python"/>

### Adding partitions

If your Airflow tasks produce time-partitioned assets, Airlift can automatically associate your materializations to the relevant partitions. In the case of `rebuild_customers_list`, data is daily partitioned in each created table, and and the Airflow DAG runs on a `@daily` cron schedule. We can likewise add a `DailyPartitionsDefinition` to each of our assets.

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe_with_partitions.py" language="python" />

Now, every time the sensor synthesizes a materialization for an asset, it will automatically have a partition associated with it.

Let's try this out by kicking off an airflow backfill for today:

```bash
airflow dags backfill rebuild_customers_list --start-date $(date +"%Y-%m-%d")
```

After this dag run completes, you should see a partitioned materialization appear in Dagster.

![Partitioned materialization in Dagster](/images/integrations/airlift/partitioned_mat.png)

Let's clear our Airflow runs so that we can kick off this backfill again for testing in the future.

```bash
airflow db clean
```

In order for partitioned assets to work out of the box with `dagster-airlift`, the following things need to be true:

- The asset can only be time-window partitioned. This means static, dynamic, and multi partitioned definitions will require custom functionality.
- The partitioning scheme must match up with the [logical_date / execution_date](https://airflow.apache.org/docs/apache-airflow/stable/faq.html#what-does-execution-date-mean) of corresponding Airflow runs. That is, each logical_date should correspond _exactly_ to a partition in Dagster.

## Next steps

Next, it's time to begin migrating our Airflow DAG code to Dagster. Follow along with the Migrate step [here](migrate).
