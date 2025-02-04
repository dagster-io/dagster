---
title: "Observing multiple Airflow instances"
sidebar_position: 200
---

At this point, you should have finished the [setup](setup) step, and now the example code set up with a fresh virtual environment, and two Airflow instances running locally. Now, we can start writing Dagster code.

## Observing the Airflow instances

We'll start by creating asset representations of our DAGs in Dagster.

Create a new shell and navigate to the root of the tutorial directory. You will need to set up the `dagster-airlift` package in your Dagster environment:

```bash
source .venv/bin/activate
uv pip install 'dagster-airlift[core]' dagster-webserver dagster
```

### Observing the `warehouse` Airflow instance

Next, we'll declare a reference to our `warehouse` Airflow instance, which is running at `http://localhost:8081`.

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_warehouse_instance" endBefore="end_warehouse_instance" />

Now, we can use the `load_airflow_dag_asset_specs` function to create asset representations of the DAGs in the `warehouse` Airflow instance:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_load_all" endBefore="end_load_all" />

Now, let's add these assets to a `Definitions` object:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_defs" endBefore="end_defs" />

Let's set up some environment variables, and then point Dagster to see the asset created from our Airflow instance:

```bash
# Set up environment variables to point to the airlift-federation-tutorial directory on your machine
export TUTORIAL_EXAMPLE_DIR=$(pwd)
export DAGSTER_HOME="$TUTORIAL_EXAMPLE_DIR/.dagster_home"
dagster dev -f airlift_federation_tutorial/dagster_defs/definitions.py
```

If we navigate to the Dagster UI (running at `http://localhost:3000`), we should see the assets created from the `warehouse` Airflow instance.

![Assets from the warehouse Airflow instance in the Dagster UI](/images/integrations/airlift/observe_warehouse.png)

There's a lot of DAGs in this instance, and we only want to focus on the `load_customers` DAG. Let's filter the assets to only include the `load_customers` DAG:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_filter" endBefore="end_filter" />

Let's instead add this asset to our `Definitions` object:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_customers_defs" endBefore="end_customers_defs" />

Now, our Dagster environment only includes the `load_customers` DAG from the `warehouse` Airflow instance.

![Assets from the warehouse Airflow instance in the Dagster UI](/images/integrations/airlift/only_load_customers.png)

Finally, we'll use a sensor to poll the `warehouse` Airflow instance for new runs. This way, whenever we get a successful run of the `load_customers` DAG, we'll see a materialization in the Dagster UI:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_sensor" endBefore="end_sensor" />

Now, we can add this sensor to our `Definitions` object:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_sensor_defs" endBefore="end_sensor_defs" />

You can test this by navigating to the Airflow UI at localhost:8081, and triggering a run of the `load_customers` DAG. When the run completes, you should see a materialization in the Dagster UI.

![Materialization of the load_customers DAG in the Dagster UI](/images/integrations/airlift/load_customers_mat.png)

### Observing the `metrics` Airflow instance

We can repeat the same process for the `customer_metrics` DAG in the `metrics` Airflow instance, which runs at `http://localhost:8082`. We'll leave this as an exercise to test your understanding.

When complete, your code should look like this:

<CodeExample path="airlift-federation-tutorial/airlift_federation_tutorial/dagster_defs/stages/observe_complete.py" />

### Adding lineage between `load_customers` and `customer_metrics`

Now that we have both DAGs loaded into Dagster, we can observe the cross-dag lineage between them. To do this, we'll use the `replace_attributes` function to add a dependency from the `load_customers` asset to the `customer_metrics` asset:

<CodeExample path="airlift-federation-tutorial/snippets/observe.py" startAfter="start_lineage" endBefore="end_lineage" />

Now, after adding the updated `customer_metrics_dag_asset` to our `Definitions` object, we should see the lineage between the two DAGs in the Dagster UI.

![Lineage between load_customers and customer_metrics in the Dagster UI](/images/integrations/airlift/dag_lineage.png)

## Next steps

Next, we'll federate the execution of our DAGs across both Airflow instances. Follow along [here](federated-execution).
