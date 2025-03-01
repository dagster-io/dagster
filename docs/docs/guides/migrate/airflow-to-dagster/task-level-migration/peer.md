---
title: "Peer your Airflow instance with a Dagster code location"
sidebar_position: 200
---

At this point, we should have finished the [setup](setup) step, and now we have the example code setup with a fresh virtual environment, and Airflow running locally. Now, we can start writing Dagster code.

We call the first stage of migration from Airflow to Dagster the "Peering" stage, at which we will "peer" the Airflow instance with a Dagster code location, which will create an asset representation of each Airflow DAG that you can view in Dagster. This process does not require any changes to your Airflow instance.

First, you will want a new shell and navigate to the same directory. You will need to set up the `dagster-airlift` package in your Dagster environment:

```bash
source .venv/bin/activate
uv pip install 'dagster-airlift[core]' dagster-webserver dagster
```

Next, create a `Definitions` object using `build_defs_from_airflow_instance`. You can use the empty `tutorial_example/dagster_defs/definitions.py` file as a starting point:

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/peer.py" language="python"/>

This function creates:

- An external asset representing each DAG. This asset is marked as materialized whenever a DAG run completes.
- A sensor that polls the Airflow instance for operational information. This sensor is responsible for creating materializations when a DAG executes. The sensor must remain on in order to properly update execution status.

Let's set up some environment variables, and then point Dagster to see the asset created from our Airflow DAG:

```bash
# Set up environment variables to point to the airlift-migration-tutorial directory on your machine
export TUTORIAL_EXAMPLE_DIR=$(pwd)
export TUTORIAL_DBT_PROJECT_DIR="$TUTORIAL_EXAMPLE_DIR/tutorial_example/shared/dbt"
export AIRFLOW_HOME="$TUTORIAL_EXAMPLE_DIR/.airflow_home"
dagster dev -f tutorial_example/dagster_defs/definitions.py
```

<img
  src="/images/integrations/airlift/peer.svg"
  alt="Peered asset in Dagster UI"
/>

Let's kick off a run of the `reubild_customers_list` DAG in Airflow.

```bash
airflow dags backfill rebuild_customers_list --start-date $(shell date +"%Y-%m-%d")
```

When this run has completed in Airflow, we should be able to navigate to the Dagster UI, and see that the Dagster has registered a materialization corresponding to that successful run.

<img
  src="/images/integrations/airlift/peer_materialize.svg"
  alt="Materialized peer asset in Dagster UI"
/>

Run the following command to clean the Airflow and Dagster run history (we just do this so we can run the same example backfill in the future). Under the hood, this just deletes runs from Airflow and asset materializations from Dagster.

```bash
make clean
```

_Note: When the code location loads, Dagster will query the Airflow REST API in order to build a representation of your DAGs. In order for Dagster to reflect changes to your DAGs, you will need to reload your code location._

## Asset checks as User Acceptance Tests

Once you have peered your Airflow DAGs in Dagster, regardless of migration progress, you can begin to add asset checks to your Dagster code. In Dagster, Asset checks can be used to validate the quality of your data assets, and can provide additional observability and value on top of your Airflow DAG even before migration starts.

Asset checks can both act as useful _user acceptance tests_ to ensure that any migration steps taken are successful, as well as _outlive_ the migration itself.

For example, we're going to add an asset check to ensure that the final `customers` CSV output exists, and has a nonzero number of rows.

<CodeExample path="airlift-migration-tutorial/tutorial_example/dagster_defs/stages/peer_with_check.py" language="python"/>

Once we reload the code location, we'll see a tab `checks` indicating the presence of an asset check on our `rebuild_customers_list` asset.

![Asset check on peer DAG](/images/integrations/airlift/asset_check_peered_dag.png)

Let's run the backfill again:

```bash
airflow dags backfill rebuild_customers_list --start-date $(shell date +"%Y-%m-%d")
```

And we'll see that the asset check executed successfully in Dagster (indicated by the green check mark).

![Asset check success](/images/integrations/airlift/peer_check_success.png)

Let's again wipe materializations and runs for tutorial purposes.

```bash
make clean
```

## Next steps

The next step is to start observing the asset dependencies within your DAG. Follow along at the Observe stage of the tutorial [here](observe)
