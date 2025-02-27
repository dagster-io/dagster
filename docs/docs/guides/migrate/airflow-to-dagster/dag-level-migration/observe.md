---
title: 'Observe the Airflow DAG'
sidebar_position: 300
---

## Observing DAG-mapped

When migrating an entire DAG at once, we'll want to create assets which map to the entire DAG. Whereas in the [task-by-task observation step](../task-level-migration/observe), we used the `assets_with_task_mappings` function, we'll instead use the `assets_with_dag_mappings` function.

For our `rebuild_customers_list` DAG, let's take a look at what the new observation code looks like:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe_dag_level.py" />

Now, instead of getting a materialization when a particular task completes, each mapped asset will receive a materialization when the entire DAG completes.