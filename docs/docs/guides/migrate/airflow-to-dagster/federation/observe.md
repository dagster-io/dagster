---
description: Create Dagster asset representations of Airflow DAGs in order to observe Airflow instances from Dagster.
sidebar_position: 200
title: Observe multiple Airflow instances from Dagster
---

In the [previous step](/guides/migrate/airflow-to-dagster/federation/setup), we installed the tutorial example code and started two Airflow instances running locally. In this step, we'll create Dagster asset representations of Airflow DAGs in order to observe the Airflow instances from Dagster.

## Install the `dagster-airlift` package in your Dagster environment

First, create a new shell and navigate to the root of the tutorial directory. You will need to install the `dagster-airlift`, `dagster-webserver`, and `dagster` packages in your Dagster environment:

```bash
source .venv/bin/activate
uv pip install 'dagster-airlift[core]' dagster-webserver dagster
```

:::note dagster-airlift API

For a full list of `dagster-airlift` classes and methods, see the [API docs](https://docs.dagster.io/api/libraries/dagster-airlift).

:::

## Observe the `warehouse` Airflow instance

Next, in your `airlift_federation_tutorial/dagster_defs/definitions.py` file, declare a reference to the `warehouse` Airflow instance, which is running at `http://localhost:8081`:

<CodeExample
  path="airlift-federation-tutorial/snippets/observe.py"
  startAfter="start_warehouse_instance"
  endBefore="end_warehouse_instance"
/>

Now you can use the `load_airflow_dag_asset_specs` function to create asset representations (<PyObject section="assets" module="dagster" object="AssetSpec" pluralize />) of the DAGs in the `warehouse` Airflow instance:

<CodeExample
  path="airlift-federation-tutorial/snippets/observe.py"
  startAfter="start_load_all"
  endBefore="end_load_all"
/>

Add these assets to a <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_defs" endBefore="end_defs" />

Next, set up some environment variables, then point Dagster to the asset created from the Airflow instance:

```bash
# Set up environment variables to point to the airlift-federation-tutorial directory on your machine
export TUTORIAL_EXAMPLE_DIR=$(pwd)
export DAGSTER_HOME="$TUTORIAL_EXAMPLE_DIR/.dagster_home"
dagster dev -f airlift_federation_tutorial/dagster_defs/definitions.py
```

If you navigate to the Dagster UI (running at `http://localhost:3000`), you should see the assets created from the `warehouse` Airflow instance:

![Assets from the warehouse Airflow instance in the Dagster UI](/images/integrations/airlift/observe_warehouse.png)

There are a lot of DAGs in this instance, but we only want to focus on the `load_customers` DAG. Filter the assets to only include the `load_customers` DAG:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_filter" endBefore="end_filter" />

Add this asset to the <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="airlift-federation-tutorial/snippets/observe.py"
  startAfter="start_customers_defs"
  endBefore="end_customers_defs"
/>

Now, your Dagster environment only includes the `load_customers` DAG from the `warehouse` Airflow instance:

![Assets from the warehouse Airflow instance in the Dagster UI](/images/integrations/airlift/only_load_customers.png)

Finally, create a [sensor](/guides/automate/sensors/) to poll the `warehouse` Airflow instance for new runs. This sensor ensures that whenever there is a successful run of the `load_customers` DAG, there will be a materialization in the Dagster UI:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_sensor" endBefore="end_sensor" />

Next, add this sensor to our <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="airlift-federation-tutorial/snippets/observe.py"
  startAfter="start_sensor_defs"
  endBefore="end_sensor_defs"
/>

You can test this by navigating to the Airflow UI at localhost:8081, and triggering a run of the `load_customers` DAG. When the run completes, you should see a materialization in the Dagster UI:

![Materialization of the load_customers DAG in the Dagster UI](/images/integrations/airlift/load_customers_mat.png)

## Observe the `metrics` Airflow instance

You can repeat the same process for the `customer_metrics` DAG in the `metrics` Airflow instance, which runs at `http://localhost:8082`. We'll leave this as an exercise to test your understanding.

:::note Complete code

To see what the code should look like after you have completed all the steps above, check out the [example in GitHub](https://github.com/dagster-io/dagster/blob/master/examples/airlift-federation-tutorial/airlift_federation_tutorial/dagster_defs/stages/observe_complete.py).

:::

## Observe the cross-DAG lineage between `load_customer` and `customer_metrics`

Now that you have both DAGs loaded into Dagster, you can observe the cross-DAG lineage between them. To do this, use the `replace_attributes` function to add a dependency from the `load_customers` asset to the `customer_metrics` asset:

<CodeExample
  path="airlift-federation-tutorial/snippets/observe.py"
  startAfter="start_lineage"
  endBefore="end_lineage"
/>

Now, after adding the updated `customer_metrics_dag_asset` to our <PyObject section="definitions" module="dagster" object="Definitions" /> object, you should see the lineage between the two DAGs in the Dagster UI:

![Lineage between load_customers and customer_metrics in the Dagster UI](/images/integrations/airlift/dag_lineage.png)

## Next steps

In the next step, "[Federate execution across Airflow instances](/guides/migrate/airflow-to-dagster/federation/federate-execution)", we'll federate the execution of our DAGs across both Airflow instances.
