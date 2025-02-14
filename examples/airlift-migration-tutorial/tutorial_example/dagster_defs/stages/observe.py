import os
from pathlib import Path

import dagster as dg
import dagster_airlift.core as dg_airlift_core
import dagster_dbt as dg_dbt


@dg.asset_check(asset=dg.AssetKey(["airflow_instance_one", "dag", "rebuild_customers_list"]))
def validate_exported_csv() -> dg.AssetCheckResult:
    csv_path = Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv"

    if not csv_path.exists():
        return dg.AssetCheckResult(
            passed=False, description=f"Export CSV {csv_path} does not exist"
        )

    rows = len(csv_path.read_text().split("\n"))
    if rows < 2:
        return dg.AssetCheckResult(
            passed=False,
            description=f"Export CSV {csv_path} is empty",
            severity=dg.AssetCheckSeverity.WARN,
        )

    return dg.AssetCheckResult(
        passed=True,
        description=f"Export CSV {csv_path} exists",
        metadata={"rows": rows},
    )


# highlight-start
# Define the dbt_project_path function to return the path to the dbt project directory
def dbt_project_path() -> Path:
    env_val = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
    assert env_val, "TUTORIAL_DBT_PROJECT_DIR must be set"
    return Path(env_val)


# Use the dbt_assets decorator to define assets for models within the dbt project automatically.
@dg_dbt.dbt_assets(
    manifest=dbt_project_path() / "target" / "manifest.json",
    project=dg_dbt.DbtProject(dbt_project_path()),
)
def dbt_project_assets(context: dg.AssetExecutionContext, dbt: dg_dbt.DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


mapped_assets = dg_airlift_core.assets_with_task_mappings(
    dag_id="rebuild_customers_list",
    task_mappings={
        # Define an AssetSpec for the csv file created by the load_raw_customers task.
        "load_raw_customers": [dg.AssetSpec(key=["raw_data", "raw_customers"])],
        # We map the assets to the build_dbt_models task which creates them Airflow-side.
        "build_dbt_models": [dbt_project_assets],
        # Define an AssetSpec for the csv file created by the export_customers task.
        "export_customers": [dg.AssetSpec(key="customers_csv", deps=["customers"])],
    },
)
# highlight-end


defs = dg_airlift_core.build_defs_from_airflow_instance(
    airflow_instance=dg_airlift_core.AirflowInstance(
        auth_backend=dg_airlift_core.AirflowBasicAuthBackend(
            webserver_url="http://localhost:8080",
            username="admin",
            password="admin",
        ),
        name="airflow_instance_one",
    ),
    defs=dg.Definitions(
        # highlight-start
        assets=mapped_assets,
        # We need to pass the dbt resource so that it can be utilized by dbt_project_assets.
        resources={"dbt": dg_dbt.DbtCliResource(project_dir=dbt_project_path())},
        # highlight-end
        asset_checks=[validate_exported_csv],
    ),
)
