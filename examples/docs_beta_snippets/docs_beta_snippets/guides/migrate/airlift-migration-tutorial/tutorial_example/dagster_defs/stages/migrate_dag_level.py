import os
from pathlib import Path

from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    AssetSpec,
    Definitions,
    materialize,
    multi_asset,
)
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    assets_with_dag_mappings,
    build_defs_from_airflow_instance,
)
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

# Code also invoked from Airflow
from tutorial_example.shared.export_duckdb_to_csv import ExportDuckDbToCsvArgs, export_duckdb_to_csv
from tutorial_example.shared.load_csv_to_duckdb import LoadCsvToDuckDbArgs, load_csv_to_duckdb


def dbt_project_path() -> Path:
    env_val = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
    assert env_val, "TUTORIAL_DBT_PROJECT_DIR must be set"
    return Path(env_val)


def airflow_dags_path() -> Path:
    return Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "tutorial_example" / "airflow_dags"


def load_csv_to_duckdb_asset(spec: AssetSpec, args: LoadCsvToDuckDbArgs) -> AssetsDefinition:
    @multi_asset(name=f"load_{args.table_name}", specs=[spec])
    def _multi_asset() -> None:
        load_csv_to_duckdb(args)

    return _multi_asset


def export_duckdb_to_csv_defs(spec: AssetSpec, args: ExportDuckDbToCsvArgs) -> AssetsDefinition:
    @multi_asset(name=f"export_{args.table_name}", specs=[spec])
    def _multi_asset() -> None:
        export_duckdb_to_csv(args)

    return _multi_asset


@dbt_assets(
    manifest=dbt_project_path() / "target" / "manifest.json",
    project=DbtProject(dbt_project_path()),
)
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


mapped_assets = assets_with_dag_mappings(
    dag_mappings={
        "rebuild_customers_list": [
            load_csv_to_duckdb_asset(
                AssetSpec(key=["raw_data", "raw_customers"]),
                LoadCsvToDuckDbArgs(
                    table_name="raw_customers",
                    csv_path=airflow_dags_path() / "raw_customers.csv",
                    duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
                    names=["id", "first_name", "last_name"],
                    duckdb_schema="raw_data",
                    duckdb_database_name="jaffle_shop",
                ),
            ),
            dbt_project_assets,
            export_duckdb_to_csv_defs(
                AssetSpec(key="customers_csv", deps=["customers"]),
                ExportDuckDbToCsvArgs(
                    table_name="customers",
                    csv_path=Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv",
                    duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
                    duckdb_database_name="jaffle_shop",
                ),
            ),
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
    ),
)


if __name__ == "__main__":
    assert dbt_project_path().exists()
    # print(dbt_project_path().absolute())
    Definitions.validate_loadable(defs)
    materialize(defs.get_asset_graph().assets_defs)
