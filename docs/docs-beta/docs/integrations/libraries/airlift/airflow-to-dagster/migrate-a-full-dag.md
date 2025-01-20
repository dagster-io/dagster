---
title: "Migrate a full DAG"
sidebar_position: 600
---

There may be DAGs for which you want to migrate the entire DAG at once rather than on a per-task basis. Some reasons for taking this approach:

- You're making use of "dynamic tasks" in Airflow, which don't conform neatly to the task mapping protocol we've laid out above.
- You want to make more substantial refactors to the DAG structure that don't conform to the existing task structure

For cases like this, we allow you to map assets to a full DAG.

## Setup

This guide assumes you've only completed the [setup](setup) and [peer](peer) steps of the Airflow migration tutorial. If you've already completed the full migration tutorial, we advise downloading a fresh copy and following along with those steps. This guide will perform the observe and migrate steps at the DAG-level instead of on a task-by-task basis, for the `rebuild_customers_list` DAG.

## Observing DAG-mapped

When migrating an entire DAG at once, we'll want to create assets which map to the entire DAG. Whereas in the [task-by-task observation step](setup), we used the `assets_with_task_mappings` function, we'll instead use the `assets_with_dag_mappings` function.

For our `rebuild_customers_list` DAG, let's take a look at what the new observation code looks like:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe_dag_level.py" />

Now, instead of getting a materialization when a particular task completes, each mapped asset will receive a materialization when the entire DAG completes.

## Migrating DAG-mapped assets

Recall that in the [task-by-task migration step](migrate), we "proxy" execution on a task by task basis, which is controlled by a yaml document. For DAG-mapped assets, execution is proxied on a per-DAG basis. Proxying execution to Dagster will require all assets mapped to that DAG be _executable_ within Dagster. Let's take a look at some fully migrated code mapped to DAGs instead of tasks:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/migrate_dag_level.py" />

Now that all of our assets are fully executable, we can create a simple yaml file to proxy execution for the whole dag:

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/rebuild_customers_list.yaml" />

We will similarly use `proxying_to_dagster` at the end of our DAG file (the code is exactly the same here as it was for the per-task migration step)

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/dags_truncated.py" />

Once the `proxied` bit is flipped to True, we can go to the Airflow UI, and we'll see that our tasks have been replaced with a single task.

![Before DAG proxying](/images/integrations/airlift/before_dag_override.png)

![After DAG proxying](/images/integrations/airlift/after_dag_override.png)

When performing dag-level mapping, we don't preserve task structure in the Airflow dags. This single task will materialize all mapped Dagster assets instead of executing the original Airflow task business logic.

We can similarly mark `proxied` back to `False`, and the original task structure and business logic will return unchanged.
