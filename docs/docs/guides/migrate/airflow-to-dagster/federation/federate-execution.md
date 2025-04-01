---
title: 'Federate execution'
sidebar_position: 300
---

In the [previous step](/guides/migrate/airflow-to-dagster/federation/observe), we created Dagster asset representations of Airflow DAGs in order to observe the Airflow instances from Dagster, and set up cross-instance lineage for the DAGs. In this step, we'll federate the execution of the DAGs across both Airflow instances by using Dagster's [Declarative Automation](/guides/automate/declarative-automation/) framework.

## Make the `customer_metrics` DAG executable

To federate execution of the `customer_metrics` Airflow DAG, you first need to make its corresponding asset executable within Dagster.

To do this, you can use the <PyObject section="assets" module="dagster" object="multi_asset" displayText="@multi_asset" /> decorator to define how the `customer_metrics` asset should be executed. You'll use the `AirflowInstance` defined earlier to trigger a run of the `customer_metrics` DAG. If the run completes successfully, the asset will be materialized. If the run fails, an exception will be raised:

<CodeExample
  path="airlift-federation-tutorial/snippets/federated_execution.py"
  startAfter="start_multi_asset"
  endBefore="end_multi_asset"
/>

Next, replace the `customer_metrics_dag_asset` in the <PyObject section="definitions" module="dagster" object="Definitions" /> object with the `run_customer_metrics` function:

<CodeExample
  path="airlift-federation-tutorial/snippets/federated_execution.py"
  startAfter="start_multi_asset_defs"
  endBefore="end_multi_asset_defs"
/>

In the Dagster UI, you should see that the `customer_metrics` asset can now be materialized.

## Federate execution

Ultimately, we would like to trigger a run of `customer_metrics` whenever `load_customers` completes successfully. We're already retrieving a materialization when `load_customers` completes, so we can use this to trigger a run of `customer_metrics` by using [Declarative Automation](/guides/automate/declarative-automation).

First, add an [`AutomationCondition.eager()`](/api/python-api/assets#dagster.AutomationCondition.eager) to the `customer_metrics_dag_asset`. This will tell Dagster to run the `run_customer_metrics` function whenever the `load_customers` asset is materialized:

<CodeExample
  path="airlift-federation-tutorial/snippets/federated_execution.py"
  startAfter="start_eager"
  endBefore="end_eager"
/>

Next, create an <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" /> to set up Declarative Automation:

<CodeExample
  path="airlift-federation-tutorial/snippets/federated_execution.py"
  startAfter="start_automation_sensor"
  endBefore="end_automation_sensor"
/>

Add this sensor to the <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="airlift-federation-tutorial/snippets/federated_execution.py"
  startAfter="start_complete_defs"
  endBefore="end_complete_defs"
/>

Now the `run_customer_metrics` function will be executed whenever the `load_customers` asset is materialized. You can test this by triggering a run of the `load_customers` DAG in Airflow. When the run completes, you should see a materialization of the `customer_metrics` asset start in the Dagster UI, and eventually a run of the `customer_metrics` DAG in the metrics Airflow instance.

:::note Complete code

To see what the code should look like after you have completed all the steps above, check out the [example in GitHub](https://github.com/dagster-io/dagster/blob/master/examples/airlift-federation-tutorial/airlift_federation_tutorial/dagster_defs/stages/executable_and_da.py).

:::

## Conclusion

That concludes the tutorial! If you followed all the steps, you should have successfully federated the execution of two DAGs across two Airflow instances using Dagster's Declarative Automation system and set up cross-instance lineage for the DAGs. You can now observe the lineage and execution of both DAGs in the Dagster UI.
