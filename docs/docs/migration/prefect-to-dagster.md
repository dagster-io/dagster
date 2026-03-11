---
title: Prefect to Dagster
description: Convert Prefect flows and tasks to Dagster assets and schedules.
last_update:
  author: Dennis Hume
sidebar_position: 500
---

Prefect flows are collections of tasks with an implicit execution order. The migration to Dagster maps each `@task` to an `@asset` and makes the dependency chain explicit with `deps`.

<Tabs>
<TabItem value="before" label="Before">

A Prefect flow with three tasks:

```python
from prefect import flow, task

@task
def fetch_data():
    return {"records": [{"id": i, "value": i * 10} for i in range(1, 6)]}

@task
def process_data(data):
    return {"total": sum(r["value"] for r in data["records"]), "count": len(data["records"])}

@task
def save_results(results):
    print(f"Saving {results['count']} records with total {results['total']}")
    return results

@flow(name="data-processing-flow")
def data_processing_flow():
    data = fetch_data()
    results = process_data(data)
    save_results(results)
```

</TabItem>
<TabItem value="after" label="After">

Three Dagster assets with a schedule:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/migrating_to_dagster/prefect_migration.py"
  language="python"
  title="src/project_mini/defs/migrating_to_dagster/prefect_migration.py"
/>

</TabItem>
</Tabs>

## Changes

**Tasks become assets, return values become `deps`.** Each Prefect `@task` becomes a `@dg.asset`. The implicit execution order inside the `@flow` function (fetch → process → save) is made explicit with `deps`. Note that unlike Prefect, where task return values flow directly into the next task's arguments, `deps` in Dagster only controls execution order—each asset reads its inputs from your storage layer rather than from an in-memory return value. If you want Dagster to manage the data handoff automatically, use an [I/O manager](/guides/build/io-managers/).

**Schedule.** The `@flow` decorator and its deployment schedule are replaced by a `@dg.schedule` wrapping a [`define_asset_job`](/api/dagster/assets#dagster.define_asset_job). Unlike a Prefect deployment, the schedule is version-controlled alongside the asset definitions and visible in the Dagster UI without a separate deployment step.

**Prefect Blocks become Dagster resources.** Prefect Blocks (database connections, API credentials, storage configs) become Dagster [resources](/guides/build/external-resources/). With Dagster, you can define a resource class, configure it per-environment in your `Definitions`, and inject it into assets in the function signature.

**Prefect automations become Dagster `@sensor` definitions.** Prefect automations that trigger flows based on events or external state become Dagster [`@sensor`](/guides/automate/sensors) definitions. A sensor polls for a condition on each tick and yields a `RunRequest` when it's met.
