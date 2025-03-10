import os
from pathlib import Path

from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetExecutionContext,
    AssetKey,
    AssetSpec,
    # highlight-start
    DailyPartitionsDefinition,
    # highlight-end
    Definitions,
    asset_check,
)
from dagster._time import get_current_datetime_midnight
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
)
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

# highlight-start
PARTITIONS_DEF = DailyPartitionsDefinition(start_date=get_current_datetime_midnight())
# highlight-end


@asset_check(asset=AssetKey(["customers_csv"]))
def validate_exported_csv() -> AssetCheckResult:
    csv_path = Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv"

    if not csv_path.exists():
        return AssetCheckResult(passed=False, description=f"Export CSV {csv_path} does not exist")

    rows = len(csv_path.read_text().split("\n"))
    if rows < 2:
        return AssetCheckResult(
            passed=False,
            description=f"Export CSV {csv_path} is empty",
            severity=AssetCheckSeverity.WARN,
        )

    return AssetCheckResult(
        passed=True,
        description=f"Export CSV {csv_path} exists",
        metadata={"rows": rows},
    )


def dbt_project_path() -> Path:
    env_val = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
    assert env_val, "TUTORIAL_DBT_PROJECT_DIR must be set"
    return Path(env_val)


@dbt_assets(
    manifest=dbt_project_path() / "target" / "manifest.json",
    project=DbtProject(dbt_project_path()),
    # highlight-start
    partitions_def=PARTITIONS_DEF,
    # highlight-end
)
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


mapped_assets = assets_with_task_mappings(
    dag_id="rebuild_customers_list",
    task_mappings={
        "load_raw_customers": [
            # highlight-start
            AssetSpec(key=["raw_data", "raw_customers"], partitions_def=PARTITIONS_DEF)
            # highlight-end
        ],
        "build_dbt_models": [dbt_project_assets],
        "export_customers": [
            # highlight-start
            AssetSpec(key="customers_csv", deps=["customers"], partitions_def=PARTITIONS_DEF)
            # highlight-end
        ],
    },
)


defs = build_defs_from_airflow_instance(
    airflow_instance=AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url="http://localhost:8080",
            username="admin",
            password="admin",
        ),
        name="airflow_instance_one",
    ),
    defs=Definitions(
        assets=mapped_assets,
        resources={"dbt": DbtCliResource(project_dir=dbt_project_path())},
        asset_checks=[validate_exported_csv],
    ),
)
