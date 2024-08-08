# Airlift

Airlift is a toolkit for observing Airflow instances from within Dagster and for accelerating the migration of Airflow DAGs to Dagster assets.

## Goals

- Observe Airflow DAGs and their execution history with no changes to Airflow code
- Model and observe assets orchestrated by Airflow with no changes to Airflow code
- (Future) Enable a migration process that
  - Can be done task-by-task in any order with minimal coordination
  - Has task-by-task rollback to reduce risk
  - That retains Airflow DAG structure and execution history during the migration

## Process

- **Peer**
  - Observe an Airflow instance from within a Dagster Deployment via the Airflow REST API.
  - This loads every Airflow DAG as an asset definition and creates a sensor that polls Airflow for execution history.
- **Observe**
  - Add a mapping that maps the airflow dag and task id to a basket of definitions that you want to observe. (e.g. render the full lineage the dbt models an Airflow task orchestrates)
  - The sensor used for peering also polls for task execution history, and adds materializations to an observed asset when its corresponding task successfully executes

## REST API Availability

Airlift depends on the the availability of Airflow’s REST API. Airflow’s REST API was made stable in its 2.0 release (Dec 2020) and was introduced experimentally in 1.10 in August 2018. Currently Airflow requires the availability of the REST API.

- **OSS:** Stable as of 2.00
- **MWAA**
  - Note: only available in Airflow 2.4.3 or later on MWAA.
  - Doesn’t appear to be a well-defined reason other than pure conservatism according to [ChatGPT](https://chatgpt.com/c/220cd63e-2111-4b32-bd83-87d95e2390d7).
- **Cloud Composer:** No limitations as far as we know.
- **Astronomer:** No limitations as far as we know.

## Peering

The first step is to peer the Dagster Deployment and the Airflow instance.

To do this you need to install airlift in and make it available in your Dagster deployment.

```bash
uv pip install dagster-airlift[core]
```

At that point you create a `Definitions` object using `build_defs_from_airflow_instance`.

```python
from dagster_airlift.core import AirflowInstance, build_defs_from_airflow_instance

defs = build_defs_from_airflow_instance(
    airflow_instance=AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080",
            username="admin",
            password="admin",
        ),
        name="airflow_instance_one",
    )
)
```

Note: When a code server is loaded for the first time it will query the target Airflow REST API. Subsequent process loads (e.g. a run worker loading) will used a cached response. If you want Dagster to pick up new DAGs, you will need restart the code server.

An MWAA auth backend is available at `dagster_airlift.mwaa.auth.MwaaSessionAuthBackend`

This function creates:

- An asset representing each DAG. This asset is “materialized” whenever a DAG run completes.
- A sensor that polls the Airflow instance for operational information. This is what keeps the DAG execution history up to date. It must be on to get timely information.

### Peering to multiple instances

Airlift supports peering to multiple Airflow instances, as you can invoke `create_airflow_instance_defs` multiple times and combine them with `Definitions.merge`

```python
from dagster_airlift.core import AirflowInstance, build_defs_from_airflow_instance

defs = build_defs_from_airflow_instance(
    airflow_instance=AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://yourcompany.com/instance_one",
            username="admin",
            password="admin",
        ),
        name="airflow_instance_one",
    )
).merge(
    build_defs_from_airflow_instance(
        airflow_instance=AirflowInstance(
            auth_backend=BasicAuthBackend(
                webserver_url="http://yourcompany.com/instance_two",
                username="admin",
                password="admin",
            ),
            name="airflow_instance_two",
        )
    )
)
```

## Observing Assets

The next step is to observe the assets that are orchestrated from Airflow. In order to do that we must create the corresponding definitions in the Dagster deployment.

We have an included example at `examples/experimental/dagster-airlift/examples/peering-with-dbt`. We suggest mimicking the structure of this project as a starting point.

To add definitions that an Airlift-enabled deployment will observed, you need to use the `orchestrated_defs` argument to `build_defs_from_airflow_instance`

_Note: This also accepts an object of type `Definitions`. We have recently added a function, `Definitions.merge`, which allows users to combine and compose `Definitions` objects, which this utilizes._

For most projects we anticipate the following process:

- Create a new factory class for every operator type or specialized use case of an operator (e.g. a BashOperator invoking a dbt project).
- Use that factory to create definitions associating with each Airflow task.

In our example we have a pre-written factory class (in `examples/experimental/dagster-airlift/dagster_airlift/dbt/multi_asset.py`) that is associated with invoking a dbt project:

```python
@dataclass
class DbtProjectDefs(DefsFactory):
    dbt_project_path: Path
    name: str
    group: Optional[str] = None

    def build_defs(self) -> Definitions:
        dbt_manifest_path = self.dbt_project_path / "target" / "manifest.json"

        @dbt_assets(manifest=json.loads(dbt_manifest_path.read_text()), name=self.name)
        def _dbt_asset(context: AssetExecutionContext, dbt: DbtCliResource):
            yield from dbt.cli(["build"], context=context).stream()

        if self.group:
            _dbt_asset = _dbt_asset.with_attributes(
                group_names_by_key={key: self.group for key in _dbt_asset.keys}
            )

        return Definitions(
            assets=[_dbt_asset],
            resources={
                "dbt": DbtCliResource(
                    project_dir=self.dbt_project_path, profiles_dir=self.dbt_project_path
                )
            },
        )
```

We imagine most people will have to customize this, so we encourage you to copy and paste it for now.

Then you can add instances of the Factory to your `build_defs_from_airflow_instance` call:

```python

defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    orchestrated_defs=defs_from_factories(
        DbtProjectDefs(
            name="dbt_dag__build_dbt_models",
            dbt_project_path=dbt_project_path(),
            group="dbt",
        ),
    ),
)
```

### Mapping assets to tasks

We default to a "convention over configuration" approach to affiliate Dagster assets with Airflow tasks.

Note the naming convention `dbt_dag__build_dbt_models`. By default we use this convention to encode the dag name (`dbt_dag`) and task id (`build_dbt_models`) of the Airflow task actually orchestrating the computation.

This name gets parsed and set corresponding tags (`airlift/dag_id` and `airlift/task_id`). Alternatively you can set those tags explicitly if you don’t want to rely on the naming convention.

Once this is done you should be able to reload your definitions and the see the full dbt project. Once you run the corresponding Airflow Dag and task, each task completion will corresponding to an asset materialization in any asset that is orchestrated by that task.

_Note: There will be some delay as this process is managed by a Dagster sensor that polls the Airflow instance for task history. This is every 30 seconds by default, so there will be some delay._
