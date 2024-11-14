import os
from pathlib import Path

from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    AssetSpec,
    DailyPartitionsDefinition,
    Definitions,
    ScheduleDefinition,
    asset_check,
    multi_asset,
)
from dagster._time import get_current_datetime_midnight
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

# Code also invoked from Airflow
from tutorial_example.shared.export_duckdb_to_csv import ExportDuckDbToCsvArgs, export_duckdb_to_csv
from tutorial_example.shared.load_csv_to_duckdb import LoadCsvToDuckDbArgs, load_csv_to_duckdb

PARTITIONS_DEF = DailyPartitionsDefinition(start_date=get_current_datetime_midnight())


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
    partitions_def=PARTITIONS_DEF,
)
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


assets = [
    load_csv_to_duckdb_asset(
        AssetSpec(key=["raw_data", "raw_customers"], partitions_def=PARTITIONS_DEF),
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
        AssetSpec(key="customers_csv", deps=["customers"], partitions_def=PARTITIONS_DEF),
        ExportDuckDbToCsvArgs(
            table_name="customers",
            csv_path=Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv",
            duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
            duckdb_database_name="jaffle_shop",
        ),
    ),
]


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


rebuild_customer_list_schedule = rebuild_customers_list_schedule = ScheduleDefinition(
    name="rebuild_customers_list_schedule",
    target=AssetSelection.assets(*assets),
    cron_schedule="0 0 * * *",
)


defs = Definitions(
    assets=assets,
    schedules=[rebuild_customer_list_schedule],
    asset_checks=[validate_exported_csv],
    resources={"dbt": DbtCliResource(project_dir=dbt_project_path())},
)
