---
description: Peer Airflow with Dagster to create asset representations of Airflow DAGs using dagster-airlift.
sidebar_position: 200
title: Peer the Airflow instance with a Dagster code location
---

In the [setup step](/guides/migrate/airflow-to-dagster/dag-level-migration/setup), we created a virtual environment, installed Dagster and the tutorial example code, and set up a local Airflow instance. Now we can start writing Dagster code.

We call the first stage of migration from Airflow to Dagster the "peering" stage, since we will "peer" the Airflow instance with a Dagster code location, which will create an asset representation of each Airflow DAG that you can view in Dagster. This step does not require any changes to your Airflow instance.

## Install `dagster-airlift`

First, you will want a new shell and navigate to the same directory. You will need to set up the `dagster-airlift` package in your Dagster environment:

```bash
source .venv/bin/activate
uv pip install 'dagster-airlift[core]' dagster-webserver dagster
```

## Create asset representations of DAGs in Dagster

Next, use the <PyObject section="libraries" module="dagster_airlift" object="core.build_defs_from_airflow_instance" displayText="build_defs_from_airflow_instance" /> function to create a `Definitions` object. Copy the following code into the empty `tutorial_example/dagster_defs/definitions.py` file:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/peer.py" language="python" />

This function creates:

- An external asset representing each Airflow DAG. This asset is marked as materialized whenever a DAG run completes.
- A [sensor](/guides/automate/sensors/) that polls the Airflow instance for operational information. This sensor is responsible for creating materializations when a DAG executes and must remain on in order to properly update execution status.

## Initiate an asset materialization in Dagster from Airflow

Next, set up some environment variables, then run `dagster dev` to start Dagster pointed at the asset created from the Airflow DAG:

```bash
# Set up environment variables to point to the airlift-migration-tutorial directory on your machine
export TUTORIAL_EXAMPLE_DIR=$(pwd)
export TUTORIAL_DBT_PROJECT_DIR="$TUTORIAL_EXAMPLE_DIR/tutorial_example/shared/dbt"
export AIRFLOW_HOME="$TUTORIAL_EXAMPLE_DIR/.airflow_home"
dagster dev -f tutorial_example/dagster_defs/definitions.py
```

<img src="/images/integrations/airlift/peer.svg" alt="Peered asset in Dagster UI" />

Initiate a run of the `reubild_customers_list` DAG in Airflow:

```bash
airflow dags backfill rebuild_customers_list --start-date $(shell date +"%Y-%m-%d")
```

When this run has completed in Airflow, you should be able to navigate to the Dagster UI and see that Dagster has registered an asset materialization corresponding to that run:

<img src="/images/integrations/airlift/peer_materialize.svg" alt="Materialized peer asset in Dagster UI" />

## Clean the Airflow and Dagster run history

Later in this tutorial, you will need to run the `rebuild_customers_list` DAG again, so go ahead and run the following command to clean the Airflow and Dagster run history. This command deletes runs from Airflow and asset materializations from Dagster:

```bash
make clean
```

:::note

When the code location loads, Dagster will query the Airflow REST API to build a representation of your DAGs. For Dagster to reflect changes to your DAGs, you will need to reload your code location.

:::

## Validate data quality with asset checks

Once you have peered your Airflow DAGs in Dagster, you can add [asset checks](/guides/test/asset-checks) to your Dagster code. In Dagster, asset checks can be used to validate the quality of your data assets, and can provide additional observability and value on top of your Airflow DAG even before you begin migration.

Asset checks can act as user acceptance tests to ensure that any migration steps taken are successful, as well as outlive the migration itself.

In this example, we're going to add an asset check to ensure that the final `customers` CSV output exists, and has a nonzero number of rows:

<CodeExample
  path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/peer_with_check.py"
  language="python"
/>

Once you reload the code location, you should see a `checks` tab indicating the presence of an asset check on the `rebuild_customers_list` asset:

![Asset check on peer DAG](/images/integrations/airlift/asset_check_peered_dag.png)

Run the backfill again:

```bash
airflow dags backfill rebuild_customers_list --start-date $(shell date +"%Y-%m-%d")
```

You should see that the asset check executed successfully in Dagster (indicated by the green check mark):

![Asset check success](/images/integrations/airlift/peer_check_success.png)

Finally, run `make clean` to delete runs and materializations:

```bash
make clean
```

## Next steps

In the next step, "[Observe an Airflow DAG](/guides/migrate/airflow-to-dagster/dag-level-migration/observe)", we'll create and observe assets that map to the entire example DAG.
