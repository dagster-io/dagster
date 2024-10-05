import os
from pathlib import Path

from dagster import AssetSpec, Definitions, materialize, multi_asset
from dagster._core.definitions.assets import AssetsDefinition
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance
from dagster_airlift.core.top_level_dag_def_api import assets_with_task_mappings

# Code also invoked from Airflow
from tutorial_example.shared.export_duckdb_to_csv import ExportDuckDbToCsvArgs, export_duckdb_to_csv
from tutorial_example.shared.load_csv_to_duckdb import LoadCsvToDuckDbArgs, load_csv_to_duckdb

from .jaffle_shop import jaffle_shop_assets, jaffle_shop_resource


def airflow_dags_path() -> Path:
    return Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "tutorial_example" / "airflow_dags"


def load_csv_to_duckdb_assets_def(spec: AssetSpec, args: LoadCsvToDuckDbArgs) -> AssetsDefinition:
    @multi_asset(name=f"load_{args.table_name}", specs=[spec])
    def _multi_asset() -> None:
        load_csv_to_duckdb(args)

    return _multi_asset


def export_duckdb_to_csv_assets_def(
    spec: AssetSpec, args: ExportDuckDbToCsvArgs
) -> AssetsDefinition:
    @multi_asset(name=f"export_{args.table_name}", specs=[spec])
    def _multi_asset() -> None:
        export_duckdb_to_csv(args)

    return _multi_asset


def rebuild_customer_list_defs() -> Definitions:
    return Definitions(
        assets=assets_with_task_mappings(
            dag_id="rebuild_customers_list",
            task_mappings={
                "load_raw_customers": [
                    load_csv_to_duckdb_assets_def(
                        AssetSpec(key=["raw_data", "raw_customers"]),
                        LoadCsvToDuckDbArgs(
                            table_name="raw_customers",
                            csv_path=airflow_dags_path() / "raw_customers.csv",
                            duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
                            names=["id", "first_name", "last_name"],
                            duckdb_schema="raw_data",
                            duckdb_database_name="jaffle_shop",
                        ),
                    )
                ],
                "build_dbt_models": [jaffle_shop_assets],
                "export_customers": [
                    export_duckdb_to_csv_assets_def(
                        AssetSpec(key="customers_csv", deps=["customers"]),
                        ExportDuckDbToCsvArgs(
                            table_name="customers",
                            csv_path=Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv",
                            duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
                            duckdb_database_name="jaffle_shop",
                        ),
                    )
                ],
            },
        ),
        resources={"dbt": jaffle_shop_resource()},
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
    defs=rebuild_customer_list_defs(),
)


if __name__ == "__main__":
    Definitions.validate_loadable(defs)
    materialize(defs.get_asset_graph().assets_defs)
