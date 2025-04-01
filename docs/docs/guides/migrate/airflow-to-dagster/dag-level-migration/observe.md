---
title: 'Observe the Airflow DAG'
sidebar_position: 300
---

When migrating an entire DAG at once, you must create assets that map to the entire DAG. To do this, you can use <PyObject section="libraries" module="dagster_airlift" object="core.assets_with_dag_mappings" displayText="assets_with_dag_mappings" />, which ensures that each mapped asset receives a materialization when the entire DAG completes.

For our `rebuild_customers_list` DAG, let's take a look at what the new observation code looks like:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/observe_dag_level.py" />

Now, instead of getting a materialization when a particular task completes, each mapped asset will receive a materialization when the entire DAG completes.

## Next steps

In the next step, "[Migrate DAG-mapped assets](/guides/migrate/airflow-to-dagster/dag-level-migration/migrate)", we will proxy execution for the entire Airflow DAG in Dagster.
