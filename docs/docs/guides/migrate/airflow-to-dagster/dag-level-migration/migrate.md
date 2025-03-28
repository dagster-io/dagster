---
title: 'Migrate DAG-mapped assets'
sidebar_position: 400
---

Previously, we completed the ["observe" stage](/guides/migrate/airflow-to-dagster/dag-level-migration/observe) of the Airflow DAG-level migration process by encoding the assets that are produced by each task. We also introduced partitioning to those assets.

In the [task-level migration step](/guides/migrate/airflow-to-dagster/task-level-migration/migrate), we "proxied" execution on a per-task basis through a YAML document. For DAG-mapped assets, execution is proxied on a per-DAG basis. Proxying execution to Dagster will require all assets mapped to that DAG be executable within Dagster. Let's take a look at some fully migrated code mapped to DAGs instead of tasks:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/migrate_dag_level.py" />

Now that all of our assets are fully executable, we can create a simple YAML file to proxy execution for the whole DAG:

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/rebuild_customers_list.yaml" />

We will similarly use `proxying_to_dagster` at the end of our DAG file. The code is exactly the same here as it is for the per-task migration step:

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/dags_truncated.py" />

Once `proxied` is changed to `True`, we can visit the Airflow UI and see that our tasks have been replaced with a single task:

![Before DAG proxying](/images/integrations/airlift/before_dag_override.png)

![After DAG proxying](/images/integrations/airlift/after_dag_override.png)

When performing DAG-level mapping, we don't preserve task structure in the Airflow DAGs. This single task will materialize all mapped Dagster assets instead of executing the original Airflow task business logic.

We can similarly change `proxied` back to `False`, and the original task structure and business logic will return unchanged.
