---
title: "Federating execution across Airflow instances"
sidebar_position: 300
---

At this point, we should be [observing our DAGs within Dagster](observe), and now we have cross-instance lineage for our DAGs. Now, we'll federate the execution of our DAGs across both Airflow instances by using Dagster's Declarative Automation system.

## Making `customer_metrics` executable

The `load_airflow_dag_asset_specs` function creates asset representations (called `AssetSpec`) of Airflow DAGs, but these assets are not executable. We need to define an execution function in Dagster in order to make them executable.

In order to federate execution of `customer_metrics`, we first need to make it executable within Dagster. We can do this by using the `@multi_asset` decorator to define how the `customer_metrics` asset should be executed. We'll use the `AirflowInstance` defined earlier to trigger a run of the `customer_metrics` DAG. We then wait for the run to complete, and if it is successful, we'll successfully materialize the asset. If the run fails, we'll raise an exception.

<CodeExample path="airlift-federation-tutorial/snippets/federated_execution.py" startAfter="start_multi_asset" endBefore="end_multi_asset" />

Now, we'll replace the `customer_metrics_dag_asset` in our `Definitions` object with the `run_customer_metrics` function:

<CodeExample path="airlift-federation-tutorial/snippets/federated_execution.py" startAfter="start_multi_asset_defs" endBefore="end_multi_asset_defs" />

We should be able to go to the Dagster UI and see that the `customer_metrics` asset can now be materialized.

## Federating execution

Ultimately, we would like to kick off a run of `customer_metrics` whenever `load_customers` completes successfully. We're already retrieving a materialization when `load_customers` completes, so we can use this to trigger a run of `customer_metrics` by using Declarative Automation. First, we'll add an `AutomationCondition.eager()` to our `customer_metrics_dag_asset`. This will tell Dagster to run the `run_customer_metrics` function whenever the `load_customers` asset is materialized.

<CodeExample path="airlift-federation-tutorial/snippets/federated_execution.py" startAfter="start_eager" endBefore="end_eager" />

Now, we can set up Declarative Automation by adding an `AutomationConditionSensorDefinition`.

<CodeExample path="airlift-federation-tutorial/snippets/federated_execution.py" startAfter="start_automation_sensor" endBefore="end_automation_sensor" />

We'll add this sensor to our `Definitions` object.

<CodeExample path="airlift-federation-tutorial/snippets/federated_execution.py" startAfter="start_complete_defs" endBefore="end_complete_defs" />

Now the `run_customer_metrics` function will be executed whenever the `load_customers` asset is materialized. Let's test this out by triggering a run of the `load_customers` DAG in Airflow. When the run completes, we should see a materialization of the `customer_metrics` asset kick off in the Dagster UI, and eventually a run of the `customer_metrics` DAG in the metrics Airflow instance.

## Complete code

When all the above steps are complete, your code should look something like this.

<CodeExample path="airlift-federation-tutorial/airlift_federation_tutorial/dagster_defs/stages/executable_and_da.py" />

## Conclusion

That concludes the tutorial! We've federated the execution of our DAGs across two Airflow instances using Dagster's Declarative Automation system. We've also set up cross-instance lineage for our DAGs, and can now observe the lineage and execution of our DAGs in the Dagster UI.
