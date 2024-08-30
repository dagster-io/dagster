import os
from pathlib import Path

from dagster import AssetSelection, AssetSpec, Definitions, ScheduleDefinition, multi_asset
from dagster_airlift.dbt import dbt_defs
from dagster_dbt import DbtProject

# Code also invoked from Airflow
from tutorial_example.shared.export_duckdb_to_csv import ExportDuckDbToCsvArgs, export_duckdb_to_csv
from tutorial_example.shared.load_csv_to_duckdb import LoadCsvToDuckDbArgs, load_csv_to_duckdb


def dbt_project_path() -> Path:
    env_val = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
    assert env_val, "TUTORIAL_DBT_PROJECT_DIR must be set"
    return Path(env_val)


def airflow_dags_path() -> Path:
    return Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "tutorial_example" / "airflow_dags"


def load_csv_to_duckdb_defs(spec: AssetSpec, args: LoadCsvToDuckDbArgs) -> Definitions:
    @multi_asset(name=f"load_{args.table_name}", specs=[spec])
    def _multi_asset() -> None:
        load_csv_to_duckdb(args)

    return Definitions(assets=[_multi_asset])


def export_duckdb_to_csv_defs(spec: AssetSpec, args: ExportDuckDbToCsvArgs) -> Definitions:
    @multi_asset(name=f"export_{args.table_name}", specs=[spec])
    def _multi_asset() -> None:
        export_duckdb_to_csv(args)

    return Definitions(assets=[_multi_asset])


def rebuild_customers_list_defs() -> Definitions:
    merged_defs = Definitions.merge(
        load_csv_to_duckdb_defs(
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
        dbt_defs(
            manifest=dbt_project_path() / "target" / "manifest.json",
            project=DbtProject(dbt_project_path().absolute()),
        ),
        export_duckdb_to_csv_defs(
            AssetSpec(key="customers_csv", deps=["customers"]),
            ExportDuckDbToCsvArgs(
                table_name="customers",
                csv_path=Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv",
                duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
                duckdb_database_name="jaffle_shop",
            ),
        ),
    )

    rebuild_customers_list_schedule = ScheduleDefinition(
        name="rebuild_customers_list_schedule",
        target=AssetSelection.assets(*merged_defs.get_asset_graph().all_asset_keys),
        cron_schedule="0 0 * * *",
    )

    return Definitions.merge(
        merged_defs,
        Definitions(schedules=[rebuild_customers_list_schedule]),
    )


defs = rebuild_customers_list_defs()
