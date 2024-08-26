# Airlift

Airlift is a toolkit for observing Airflow instances from within Dagster and for accelerating the migration of Airflow DAGs to Dagster assets.

## Goals

- Observe Airflow DAGs and their execution history with no changes to Airflow code
- Model and observe assets orchestrated by Airflow with no changes to Airflow code
- Enable a migration process that
  - Can be done task-by-task in any order with minimal coordination
  - Has task-by-task rollback to reduce risk
  - That retains Airflow DAG structure and execution history during the migration

## Process

- **Peer**
  - Observe an Airflow instance from within a Dagster Deployment via the Airflow REST API.
  - This loads every Airflow DAG as an asset definition and creates a sensor that polls Airflow for execution history.
- **Observe**
  - Add a mapping that maps the Airflow DAG and task id to a basket of definitions that you want to observe. (e.g. render the full lineage the dbt models an Airflow task orchestrates)
  - The sensor used for peering also polls for task execution history, and adds materializations to an observed asset when its corresponding task successfully executes
- **Migrate**
  - Selectively move execution of Airflow tasks to Dagster Software Defined Assets

## Compatibility

### REST API Availability

Airlift depends on the the availability of Airflow’s REST API. Airflow’s REST API was made stable in its 2.0 release (Dec 2020) and was introduced experimentally in 1.10 in August 2018. Currently Airflow requires the availability of the REST API.

- **OSS:** Stable as of 2.00
- **MWAA**
  - Note: only available in Airflow 2.4.3 or later on MWAA.
- **Cloud Composer:** No limitations as far as we know.
- **Astronomer:** No limitations as far as we know.

# Guide

In the below guide, we'll be working with a sample project, found in [`examples/tutorial-example`](./examples/tutorial-example/).

## Running airflow locally

The tutorial example involves running an airflow instance, and making some changes to its constituent dags. 
We can run this airflow example locally by following the following commands:
<<ADD HERE>>

To check the installation, navigate to localhost:8080, and login using `admin` for both username and password. You should see one dag appear called `rebuild_customers_list`.

Now, we're ready to start migrating.

## Step 1: Peer

### Overview and installation
The first step in our migration process is to peer the Dagster code location and the Airflow instance, which will create an asset representation of each of your Airflow DAGs in Dagster. 
- This process does not require any changes to your Airflow instance.
- Each time the Airflow DAG completes successfully, a new materialization will appear in Dagster for the corresponding asset. _Failures and in progress runs are currently not represented._

Let's peer our locally running airflow instance.

First, you will need to install `dagster-airlift[core]`, which contains the core migration tooling that we'll be using in this guide.

```bash
pip install uv
uv pip install dagster-airlift[core] dagster-webserver
```

### Code example

In order to peer our airflow instance, we'll declare a reference to it using the dagster-airlift abstraction `AirflowInstance`.
```python
from dagster_airlift.core import AirflowInstance, BasicAuthBackend

airflow_instance = AirflowInstance(
    # other backends available (e.g. MwaaSessionAuthBackend)
    auth_backend=BasicAuthBackend(
        webserver_url="http://localhost:8080",
        username="admin",
        password="admin",
    ),
    name="airflow_instance_one",
)
```

You'll notice that we've included an authorization backend here. This is equivalent to the default airflow "session" auth backend, 
but different airflow backends will have different auth mechanisms. For example, we also have a `MwaaSessionAuthBackend` for AWS MWAA, 
which is available in `dagster-airlift[mwaa]`.

We'll now call the function `build_defs_from_airflow_instance`, which will construct dagster `Definitions` corresponding to the airflow
instance.

```python
from dagster_airlift.core import build_defs_from_airflow_instance

defs = build_defs_from_airflow_instance(airflow_instance=airflow_instance)
```

This function creates:

- An external asset representing each DAG. This asset is marked as materialized whenever a DAG run completes.
- A sensor that polls the Airflow instance for operational information. This sensor is responsible for creating materializations when a DAG executes, 
    and running asset checks when there are new runs of the targeted assets. The sensor must remain on in order to properly update execution status.

The completed code for this step can be found in <<ADD NAME OF FILE>>. Here's what it looks like:
```python
COMPLETED CODE HERE
```

### Running the peering step locally

Let's run dagster to show the peered dags.

First, we need to install `dagster-webserver`, which will allow us to run the dagster UI and backend locally.

```bash
pip install uv
uv pip install dagster-webserver
```

Let's point dagster at our peering code. 
```bash
dagster dev -f <<PEERING FILE HERE>>
```

You should now be able to navigate to the Dagster UI, which is running at `localhost:3030`. Find the global asset lineage at <<link here>>, and see an asset for `rebuild_customers_list` appear. 
Dagster automatically pulls in some metadata about the underlying DAG for convenience:
- A formatted blob of source code describing the DAG.
- A link back to the airflow DAG UI.
- A raw dictionary describing the dag as returned from the REST API. The exact response can be viewed [here](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_dags) (may vary depending on airflow version)

### Dag runs as materializations

As mentioned earlier, each successful dag run will appear as a materialization in Dagster. We can demonstrate this by navigating to the airflow UI (running at localhost:8080), login with username `admin` and password `admin`, and kicking off a run of our dag (click the "play" button to the right of the dag's name). 

Navigate back to the Dagster UI <<link to asset lineage here>> and see that the corresponding asset is now marked as `materialized`. If we click on this materialization, we'll see some metadata appear:
- A link to the run in the Airflow UI
- The start and end time of the run (local timezone)

_Note: When the code location loads, Dagster will query the Airflow REST API in order to build a representation of your DAGs. In order for Dagster to reflect changes to your DAGs, you will need to reload your code location._

<details>
<summary>
*Peering to multiple instances*
</summary>

Airlift supports peering to multiple Airflow instances, as you can invoke `create_airflow_instance_defs` multiple times and combine them with `Definitions.merge`:

```python
from dagster import Definitions

from dagster_airlift.core import AirflowInstance, build_defs_from_airflow_instance

defs = Definitions.merge(
    build_defs_from_airflow_instance(
        airflow_instance=AirflowInstance(
            auth_backend=BasicAuthBackend(
                webserver_url="http://yourcompany.com/instance_one",
                username="admin",
                password="admin",
            ),
            name="airflow_instance_one",
        )
    ),
    build_defs_from_airflow_instance(
        airflow_instance=AirflowInstance(
            auth_backend=BasicAuthBackend(
                webserver_url="http://yourcompany.com/instance_two",
                username="admin",
                password="admin",
            ),
            name="airflow_instance_two",
        )
    ),
)
```

We'll be working with a single airflow instance for the remainder of the tutorial for simplicity's sake.
</details>

## Step 2: Observing Assets

Airlift allows for observing data assets that are being orchestrated from Airflow DAGs. This observation step allows you to take advantage of Dagster-native functionality before you move compute to Dagster.
- Assets show up in Dagster's data catalog
- Execute asset checks within Dagster
- Hook into Dagster's automation automatically to execute downstream assets

### Identifying assets in airflow

First, we need to identify what the underlying data assets are within our DAG. In our example DAG `rebuild_customers_list`, we have three sequential tasks:

1. `load_raw_customers` loads a CSV file of raw customer data into duckdb.
2. `run_dbt_model` builds a series of dbt models (from [jaffle shop](https://github.com/dbt-labs/jaffle_shop_duckdb)) combining customer, order, and payment data.
3. `export_customers` exports a CSV representation of the final customer file from duckdb to disk.

### Observing our first asset

Let's zoom into `load_raw_customers`. The underlying data asset produced by this task is a table in a duckdb warehouse. The table is called `raw_customers`, and exists in a schema called `raw_data`.

We'll declare an asset using Dagster's `AssetSpec` to represent this table.
```python
from dagster import AssetSpec

# Asset key in Dagster is a unique identifier with semantic meaning. In this case, we use the schema name and table name as the asset key, which should be unique for this table.
raw_customers = AssetSpec(key=["raw_data", "raw_customers"])
```

Next, we want to "link" this asset to the underlying task which computes it. We can do this using `dag_defs` and `task_defs` from `dagster-airlift`.
```python
from dagster_airlift.core import dag_defs, task_defs

defs = dag_defs(
    "rebuild_customers_list", # DAG ID which contains the task
    task_defs(
        "load_raw_customers", raw_customers # Task which produces the asset
    ),
)
```

Under the hood, this is just setting the tags `airlift/dag_id` and `airlift/task_id` on the underlying asset, which tell `build_defs_from_airflow_instance` to link runs of the task
as materializations of the tagged asset. 

Now, let's provide these defs back to our `build_defs_from_airflow_instance` function to see this linkage take place. The complete code (can be found in <<file_path_here>>):
```python
<<COMPLETE CODE HERE>>
```

We should be able to run `dagster dev` again, and see `raw_data/raw_customers` show up as an asset. 

```bash
dagster dev -f <<path_to_completed_step>> 
```

Navigate back to the global asset lineage <<link here>>; and see the `raw_data/raw_customers` asset, which is downstream of our dag's asset.

Dagster collects some convenience metadata for the observed asset:
- A link back to the airflow task UI.
- A raw dictionary describing the task as returned from the REST API. The exact response can be viewed [here](https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_task)

### Task runs as materializations

If we kick off a run of the dag, we'll now see a materialization pop up for both `raw_data/raw_customers` and our dag asset.

Navigate back to the Airflow UI running at `localhost:8080`, and again kick off a run of the DAG.
In the Dagster UI, in the global asset lineage, we should now see both the `raw_data/raw_customers` asset as well as the dag asset showing up as materialized. If we click on the materialization for our new asset, we'll see the following metadata appear:
- A link back to the airflow run
- A link to the logs for this task
- Execution start and end date (in local timezone)

At this point, we've successfully observed our first asset from airflow. 

### AssetSpec factories

Constructing an `AssetSpec` per task can be very tedious for large codebases. Oftentimes, it makes more sense to construct a common factory method that can be used to construct an `AssetSpec` from the same information you use to construct the airflow task, instead of rederiving it every time.

Let's take a look at how to do this for our `raw_data/raw_customers` asset.
If we look at the code for the underlying task, `load_raw_customers` we can see that we use a custom operator `LoadCSVToLakehouse` which, from a provided csv path and db path, is able to derive the table name and schema:
```python
<<code for the pre-shared LoadCSVToLakehouse here>>
```

We can use these same utilities for deriving the AssetSpec:
```python
<<factory to derive asset spec here>>
```

Finally, you should be able to replace the `AssetSpec` invocation with an invocation of this factory:
```python
<<invocation of dag_defs with factory here>>
```

Notice that this same factory can now be used to observe any task which uses the `LoadCSVToLakehouse` operator, with the AssetSpec automatically derived.

_Note: Any time you are using a custom operator, consider making a corresponding AssetSpec factory. This small amount of up-front work will reduce the scaling of the migration from the number of tasks to the number of operators (which is generally much lower)._

### DBT AssetSpecs

`dagster-airlift` provides some out-of-the-box AssetSpec factories for common use cases. Airlift's `dbt_defs` function is one such example, which can be used to observe any dbt models being built by an airflow task. 

######### END OF CHRIS PROGRESS ##############


The first and third tasks involve a single table each. We can manually construct `AssetSpec`s that match the assets which they build. `dagster-airlift.core` provides the `dag_defs` and `task_defs` utilities to annotate asset specs with the tasks that produce them. These annotated specs are then
provided to the `defs` argument to `build_defs_from_airflow_instance`.

```python
from dagster import AssetSpec

from dagster_airlift.core import build_defs_from_airflow_instance, dag_defs, task_defs

defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=dag_defs(
        "rebuild_customers_list",
        task_defs(
            "load_raw_customers",
            AssetSpec(key=["raw_data", "raw_customers"])
        ),
        # encode dependency on customers output
        task_defs(
            "export_customers",
            AssetSpec(key="customers_csv", deps=["customers"])
        ),
    )
)
```

To build assets for our dbt invocation, we can use the Dagster-supplied factory `dbt_defs`, installable via `uv pip install dagster-airlift[dbt]`. This will load each dbt model as its own asset:

```python
from dagster import AssetSpec
from dagster_airlift.core import build_defs_from_airflow_instance, dag_defs, task_defs
from dagster_dbt import DbtProject

defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=dag_defs(
        "rebuild_customers_list",
        task_defs(
            "load_raw_customers",
            AssetSpec(key=["raw_data", "raw_customers"])
        ),
        # encode dependency on customers output
        task_defs(
            "export_customers",
            AssetSpec(key="customers_csv", deps=["customers"])
        ),
        task_defs(
            "build_dbt_models",
            dbt_defs(
                manifest=dbt_project_path() / "target" / "manifest.json",
                project=DbtProject(dbt_project_path()),
            ),
        ),
    ),
)
```

### Mapping assets to tasks

The `from_task` and `from_dag` utilities link created assets to their underlying tasks. Assets which are properly linked will be materialized by the Airlift sensor once the corresponding task completes.

### Viewing observed assets

Once your assets are set up, you should be able to reload your Dagster definitions and see a full representation of the dbt project and other data assets in your code.

Kicking off a run of the DAG, you should see the newly created assets materialize in Dagster.

_Note: There will be some delay between task completion and assets materializing in Dagster, managed by the sensor. This sensor runs every 30 seconds by default (you can reduce down to one second via the `minimum_interval_seconds` argument to `sensor`), so there will be some delay._

## Migrating Assets

Once you have created corresponding definitions in Dagster to your Airflow tasks, you can begin to selectively migrate execution of some or all of these assets to Dagster.

To begin migration on a DAG, first you will need a file to track migration progress. In your Airflow DAG directory, create a `migration_state` folder, and in it create a yaml file with the same name as your DAG. The included example at [`examples/tutorial-example/airflow_dags/migration_state`](.examples/tutorial-example/airflow_dags/migration_state) can be used as reference.

Given our example DAG `rebuild_customers_list` with three tasks, `load_raw_customers`, `run_dbt_model`, and `export_customers`, `migration_state/rebuild_customers_list.yaml` should look like the following:

```yaml
tasks:
  load_raw_customers:
    migrated: False
  run_dbt_model:
    migrated: False
  export_customers:
    migrated: False
```

Next, you will need to modify your Airflow DAG to make it aware of the migration status:

```python
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.migration_state import load_migration_state_from_yaml
from pathlib import Path
from airflow import DAG

dag = DAG("rebuild_customers_list")
...

mark_as_dagster_migrating(
    global_vars=globals(),
    migration_state=load_migration_state_from_yaml(
        Path(__file__).parent / "migration_state"
    ),
)
```

The DAG will now display its migration state in the Airflow UI.

### Migrating individual tasks

In order to migrate a task, you must do two things:

1. First, ensure all associated assets are executable in Dagster by providing asset definitions in place of bare `AssetSpec`s.
2. The `migrated: False` status in the `migration_state` YAML folder must be adjusted to `migrated: True`.

Any task marked as migrated will use the `DagsterOperator` when executed as part of the DAG. This operator will use the Dagster GraphQL API to initiate a Dagster run of the assets corresponding to the task.

The migration file acts as the source of truth for migration status. A task which has been migrated can be toggled back to run in Airflow (for example, if a bug in implementation was encountered) simply by editing the file to `migrated: False`.

#### Migrating common operators

For some common operator patterns, like our dbt operator, Dagster supplies factories to build software defined assets for our tasks:

```python
from dagster_airlift.core import build_defs_from_airflow_instance, dag_defs, task_defs
from dagster_dbt import DbtProject

defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=dag_defs(
        "rebuild_customers_list",
        ...,
        task_defs(
            "build_dbt_models",
            dbt_defs(
                manifest=dbt_project_path() / "target" / "manifest.json",
                project=DbtProject(dbt_project_path()),
            ),
        ),
    )
)
```

#### Migrating custom operators

For all other operator types, we recommend creating a new factory class whose arguments match the inputs to your Airflow operator. Then, you can use this factory to build definitions for each Airflow task.

For example, our `load_raw_customers` task uses a custom `LoadCSVToDuckDB` operator. We'll define a function `load_csv_to_duckdb_defs` factory to build corresponding software-defined assets:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dagster import AssetSpec, Definitions, multi_asset
from dagster_airlift.core import build_defs_from_airflow_instance, dag_defs, task_defs

from tutorial_example.shared.load_csv_to_duckdb import load_csv_to_duckdb

def load_csv_to_duckdb_defs(
    table_name: str,
    csv_path: Path,
    duckdb_path: Path,
    column_names: List[str],
    duckdb_schema: str,
    duckdb_database_name: str,
) -> Definitions:
    @multi_asset(specs=[AssetSpec(key=[duckdb_schema, table_name])])
    def _multi_asset() -> None:
        load_csv_to_duckdb(
            table_name=table_name,
            csv_path=csv_path,
            duckdb_path=duckdb_path,
            names=column_names,
            duckdb_schema=duckdb_schema,
            duckdb_database_name=duckdb_database_name,
        )

    return Definitions(assets=[_multi_asset])

defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=dag_defs(
        "rebuild_customers_list",
        ...,
        task_defs(
            "load_raw_customers",
            load_csv_to_duckdb_defs(
                table_name="raw_customers",
                csv_path=Path(__file__).parent.parent / "airflow_dags" / "raw_customers.csv",
                duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
                column_names=[
                    "id",
                    "first_name",
                    "last_name",
                ],
                duckdb_schema="raw_data",
                duckdb_database_name="jaffle_shop",
            ),
        )
        ...
    ),
)
```
