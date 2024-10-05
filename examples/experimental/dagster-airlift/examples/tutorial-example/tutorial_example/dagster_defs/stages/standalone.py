import os
from pathlib import Path

from dagster import AssetSpec, Definitions, ScheduleDefinition, multi_asset
from dagster._core.definitions.assets import AssetsDefinition

# Code also invoked from Airflow
from tutorial_example.shared.export_duckdb_to_csv import ExportDuckDbToCsvArgs, export_duckdb_to_csv
from tutorial_example.shared.load_csv_to_duckdb import LoadCsvToDuckDbArgs, load_csv_to_duckdb

from .jaffle_shop import jaffle_shop_assets, jaffle_shop_resource


def dbt_project_path() -> Path:
    env_val = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
    assert env_val, "TUTORIAL_DBT_PROJECT_DIR must be set"
    return Path(env_val)


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


defs = Definitions(
    assets=[
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
        ),
        jaffle_shop_assets,
        export_duckdb_to_csv_assets_def(
            AssetSpec(key="customers_csv", deps=["customers"]),
            ExportDuckDbToCsvArgs(
                table_name="customers",
                csv_path=Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv",
                duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
                duckdb_database_name="jaffle_shop",
            ),
        ),
    ],
    resources={"dbt": jaffle_shop_resource()},
    schedules=[
        ScheduleDefinition(
            name="rebuild_customers_list_schedule",
            target="*",
            cron_schedule="0 0 * * *",
        )
    ],
)
