---
title: 'Migrate Airflow tasks'
sidebar_position: 400
---

Previously, we completed the ["observe" stage](/guides/migrate/airflow-to-dagster/task-level-migration/observe) of the Airflow migration process by encoding the assets that are produced by each task. We also introduced partitioning to those assets.

So far, we have left the Airflow code alone, but in this step, we will begin the actual migration process, which will require modifying Airflow code.

Once you have created corresponding Dagster assets for your Airflow tasks, you can proxy execution to Dagster on a per-task basis while Airflow is still controlling scheduling and orchestration. Once a task has been proxied, Airflow will kick off materializations of corresponding Dagster assets in place of executing the business logic of that task.

## Create a file to track proxying state

To begin proxying tasks in an Airflow DAG, you will first need to create a file to track proxying state.

For this tutorial, in the example Airflow DAG directory, create a `proxied_state` folder. In that folder, create a YAML file with the same name as the example DAG. The included example at `airflow_dags/proxied_state` is used by `make airflow_run`, and can be used as a template for your own proxied state files.

Given our example `rebuild_customers_list` DAG with its three tasks, `load_raw_customers`, `run_dbt_model`, and `export_customers`, your `proxied_state/rebuild_customers_list.yaml` file should look like the following:

<CodeExample
  path="airlift-migration-tutorial/tutorial_example/airflow_dags/proxied_state/rebuild_customers_list.yaml"
  language="yaml"
/>

Next, you will need to modify your Airflow DAG to make it aware of the proxied state. This is already done in the example DAG:

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/dags_truncated.py" language="python" />

Set `PROXYING` to `True` or eliminate the `if` statement.

The DAG will now display its proxied state in the Airflow UI. (There is some latency as Airflow evaluates the Python file periodically.)

![Migration state rendering in Airflow UI](/images/integrations/airlift/state_in_airflow.png)

## Migrate individual tasks

In order to proxy a task, you must do two things:

1. Ensure all associated assets are executable in Dagster by providing asset definitions in place of bare asset specs.
2. Set the `proxied: False` status in the `proxied_state` YAML folder to `proxied: True`.

Any task marked as proxied will use the <PyObject section="libraries" module="dagster_airlift" object="in_airflow.DefaultProxyTaskToDagsterOperator" displayText="DefaultProxyTaskToDagsterOperator" /> when executed as part of the DAG. This operator will use the [Dagster GraphQL API](/guides/operate/graphql/) to initiate a Dagster run of the assets corresponding to the task.

The proxied file acts as the source of truth for proxied state. The information is attached to the DAG and then accessed by Dagster via the REST API.

A task which has been proxied can be easily toggled back to run in Airflow (for example, if a bug in implementation was encountered) simply by editing the file to `proxied: False`.

## Migrate common operators

For some common operator patterns, like our `dbt` operator, Dagster supplies factories to build software-defined assets for our tasks. In fact, the <PyObject section="libraries" module="dagster_dbt" object="dbt_assets" decorator /> decorator used earlier already backs its assets with definitions, so we can change the proxied state of the `build_dbt_models` task to `proxied: True` in the proxied state file:

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/dbt_proxied.yaml" language="yaml" />

:::info

It may take up to 30 seconds for the proxied state in the Airflow UI to reflect this change. You must subsequently reload the definitions in Dagster via the UI or by restarting `dagster dev`.

:::

You can now run the `rebuild_customers_list` DAG in Airflow, and the `build_dbt_models` task will be executed in a Dagster run:

![dbt build executing in Dagster](/images/integrations/airlift/proxied_dag.png)

You'll note that we proxied a task in the middle of the Airflow DAG. The Airflow DAG structure and execution history is stable in the Airflow UI, but execution of `build_dbt_models` has moved to Dagster.

## Migrate the remaining custom operators

For all other operator types, we will need to build our own asset definitions. We recommend creating a factory function whose arguments match the inputs to your Airflow operator. Then, you can use this factory to build definitions for each Airflow task.

For example, our `load_raw_customers` task uses a custom `LoadCSVToDuckDB` operator. We'll define a function `load_csv_to_duckdb_defs` factory to build corresponding software-defined assets. Similarly for `export_customers` we'll define a function `export_duckdb_to_csv_defs` to build software-defined assets:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/migrate.py" language="python" />

We can then toggle the proxied state of the remaining tasks in the `proxied_state` file:

<CodeExample path="airlift-migration-tutorial/tutorial_example/snippets/all_proxied.yaml" language="yaml" />

## Next steps

In the next step, "[Decommission the Airflow DAG](/guides/migrate/airflow-to-dagster/task-level-migration/decommission)", we will remove the DAG from the Airflow directory and update the Dagster code to remove task associations and attach the assets to a schedule.
