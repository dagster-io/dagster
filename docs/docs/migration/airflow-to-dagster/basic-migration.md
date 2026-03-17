---
title: Basic Airflow migration
description: Manually rewrite Airflow DAGs as native Dagster assets and schedules.
last_update:
  author: Dennis Hume
sidebar_position: 10
---

This guide covers manually rewriting Airflow DAGs as native Dagster assets. This approach works well for a small number of DAGs and produces first-class Dagster assets with materialization history and staleness tracking.

:::tip Large Airflow migrations
For larger migrations, the [`dagster-airflow`](/migration/airflow-to-dagster/airflow-component-tutorial) library can convert Airflow operators directly to Dagster assets, letting you run your existing DAG code inside Dagster with minimal changes. The tradeoff: you get Dagster run history and scheduling, but assets produced this way may lack full native features like fine-grained materialization history and staleness tracking compared to a manual rewrite.
:::

<Tabs>
<TabItem value="before" label="Before">

An Airflow DAG with three tasks and a daily schedule:

```python
from airflow.decorators import dag, task
from datetime import datetime, timedelta

@task
def fetch_data(source: str = "api") -> dict:
    return {"source": source, "data": [1, 2, 3, 4, 5]}

@task
def process_data(data: dict) -> dict:
    return {"source": data["source"], "processed": [x * 2 for x in data["data"]]}

@task
def save_results(processed: dict) -> str:
    return f"Saved {len(processed['processed'])} items from {processed['source']}"

@dag(
    dag_id="simple_sequential_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="0 9 * * *",
    catchup=False,
    tags=["example", "sequential"],
    default_args={"retries": 3, "retry_delay": timedelta(minutes=5)},
)
def simple_sequential_pipeline():
    data = fetch_data()
    processed = process_data(data)
    save_results(processed)

dag_instance = simple_sequential_pipeline()
```

</TabItem>
<TabItem value="after" label="After">

Three Dagster assets with a schedule:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/migrating_to_dagster/airflow_migration.py"
  language="python"
  title="src/project_mini/defs/migrating_to_dagster/airflow_migration.py"
/>

</TabItem>
</Tabs>

## Changes

**Tasks become assets.** Each Airflow `@task` becomes a `@dg.asset`.

** XCom becomes `deps`.** Airflow passes data between tasks through XCom (serialized values in the metadata database). Dagster uses `deps`, which declare execution order, not data transfer. When the `process_data` asset declares `deps=[fetch_data]`, Dagster ensures the `fetch_data` asset materializes first, but `process_data` reads its inputs from your storage layer (a database, S3, etc.), not from a return value. If you want Dagster to handle the handoff automatically, declare the upstream asset as a function parameter and configure an [I/O manager](/guides/build/io-managers).

**Retry policy moves to the asset.** The DAG-level `default_args` retries become a [`RetryPolicy`](/api/dagster/ops#dagster.RetryPolicy) attached directly to the asset that needs it.

**Airflow DAG tags become Dagster group names and tags.** DAG tags map to `group_name` and `tags` on each asset, giving you the same grouping in the Dagster UI.

**Schedule.** The `@dag(schedule="0 9 * * *")` becomes a <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator /> wrapping a <PyObject section="assets" module="dagster" object="define_asset_job" /> that selects the three assets.

**Airflow Connections become Dagster resources.** Airflow Connections (database URLs, API credentials stored in the Airflow metadata DB) become Dagster [resources](/guides/build/external-resources/). You can define a resource class and inject it into your assets in the function signature—the equivalent of `Variable.get()` or `BaseHook.get_connection()` is a resource attribute read at runtime.

**Airflow sensors become Dagster `@sensor` definitions.** Airflow `ExternalTaskSensor` and `FileSensor` become Dagster [`@sensor`](/guides/automate/sensors) definitions. A sensor polls for a condition and yields a `RunRequest` when it's met—the same pattern, but version-controlled alongside your asset code.

:::note
**Backfill behavior.** Airflow's `catchup=True` is the default; Dagster doesn't have a direct equivalent. If you need historical backfills, trigger them explicitly using [backfill](/guides/build/partitions-and-backfills/backfilling-data).
:::
