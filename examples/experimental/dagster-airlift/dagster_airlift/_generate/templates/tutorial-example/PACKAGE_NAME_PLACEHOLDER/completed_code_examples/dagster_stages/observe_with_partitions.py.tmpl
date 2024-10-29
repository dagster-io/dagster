import os
from pathlib import Path

# start_create_partitions
from dagster import AssetExecutionContext, AssetSpec, DailyPartitionsDefinition, Definitions
from dagster._time import get_current_datetime_midnight
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
)
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

# Pick your current date for the start date here.
PARTITIONS_DEF = DailyPartitionsDefinition(start_date="2024-10-28")
# end_create_partitions

# we'll create the same thing but with the _actual_ current datetime for testing purposes.
PARTITIONS_DEF = DailyPartitionsDefinition(start_date=get_current_datetime_midnight())


def dbt_project_path() -> Path:
    env_val = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
    assert env_val, "TUTORIAL_DBT_PROJECT_DIR must be set"
    return Path(env_val)


# start_partitioned_assets
raw_customers_spec = AssetSpec(key=["raw_data", "raw_customers"], partitions_def=PARTITIONS_DEF)
export_customers_spec = AssetSpec(
    key="customers_csv", deps=["customers"], partitions_def=PARTITIONS_DEF
)


@dbt_assets(
    manifest=dbt_project_path() / "target" / "manifest.json",
    project=DbtProject(dbt_project_path()),
    partitions_def=PARTITIONS_DEF,
)
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# end_partitioned_assets


mapped_assets = assets_with_task_mappings(
    dag_id="rebuild_customers_list",
    task_mappings={
        "load_raw_customers": [
            AssetSpec(key=["raw_data", "raw_customers"], partitions_def=PARTITIONS_DEF)
        ],
        "build_dbt_models": [dbt_project_assets],
        "export_customers": [
            AssetSpec(key="customers_csv", deps=["customers"], partitions_def=PARTITIONS_DEF)
        ],
    },
)


defs = build_defs_from_airflow_instance(
    airflow_instance=AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080",
            username="admin",
            password="admin",
        ),
        name="airflow_instance_one",
    ),
    defs=Definitions(
        assets=mapped_assets,
        resources={"dbt": DbtCliResource(project_dir=dbt_project_path())},
    ),
)
