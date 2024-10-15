# Define the default arguments for the DAG
import os
from datetime import timedelta
from pathlib import Path
from typing import List, Optional

from airflow import DAG
from airflow.models.operator import BaseOperator
from airflow.operators.bash import BashOperator
from dagster._time import get_current_datetime_midnight
from dagster_airlift.in_airflow import proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml
from tutorial_example.shared.export_duckdb_to_csv import ExportDuckDbToCsvArgs, export_duckdb_to_csv
from tutorial_example.shared.load_csv_to_duckdb import LoadCsvToDuckDbArgs, load_csv_to_duckdb


class LoadCSVToDuckDB(BaseOperator):
    def __init__(
        self,
        table_name: str,
        csv_path: Path,
        duckdb_path: Path,
        column_names: List[str],
        duckdb_schema: str,
        duckdb_database_name: str,
        *args,
        **kwargs,
    ):
        self._table_name = table_name
        self._csv_path = csv_path
        self._duckdb_path = duckdb_path
        self._column_names = column_names
        self._duckdb_schema = duckdb_schema
        self._duckdb_database_name = duckdb_database_name
        super().__init__(*args, **kwargs)

    def execute(self, context) -> None:
        load_csv_to_duckdb(
            LoadCsvToDuckDbArgs(
                table_name=self._table_name,
                csv_path=self._csv_path,
                duckdb_path=self._duckdb_path,
                names=self._column_names,
                duckdb_schema=self._duckdb_schema,
                duckdb_database_name=self._duckdb_database_name,
            )
        )


class ExportDuckDBToCSV(BaseOperator):
    def __init__(
        self,
        table_name: str,
        csv_path: Path,
        duckdb_path: Path,
        duckdb_database_name: str,
        *args,
        duckdb_schema: Optional[str] = None,
        **kwargs,
    ):
        self._table_name = table_name
        self._csv_path = csv_path
        self._duckdb_path = duckdb_path
        self._duckdb_schema = duckdb_schema
        self._duckdb_database_name = duckdb_database_name
        super().__init__(*args, **kwargs)

    def execute(self, context) -> None:
        export_duckdb_to_csv(
            ExportDuckDbToCsvArgs(
                table_name=self._table_name,
                csv_path=self._csv_path,
                duckdb_path=self._duckdb_path,
                duckdb_database_name=self._duckdb_database_name,
            )
        )


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": get_current_datetime_midnight(),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}
DBT_DIR = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
# Create the DAG with the specified schedule interval
dag = DAG(
    "rebuild_customers_list",
    default_args=default_args,
    schedule="@daily",
    is_paused_upon_creation=False,
)


load_raw_customers = LoadCSVToDuckDB(
    task_id="load_raw_customers",
    dag=dag,
    table_name="raw_customers",
    csv_path=Path(__file__).parent / "raw_customers.csv",
    duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
    column_names=[
        "id",
        "first_name",
        "last_name",
    ],
    duckdb_schema="raw_data",
    duckdb_database_name="jaffle_shop",
)


args = f"--project-dir {DBT_DIR} --profiles-dir {DBT_DIR}"
run_dbt_model = BashOperator(task_id="build_dbt_models", bash_command=f"dbt build {args}", dag=dag)

export_customers = ExportDuckDBToCSV(
    task_id="export_customers",
    dag=dag,
    duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
    duckdb_database_name="jaffle_shop",
    table_name="customers",
    csv_path=Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv",
)

load_raw_customers >> run_dbt_model >> export_customers  # type: ignore

# Set this to True to begin the proxying process
PROXYING = False

if PROXYING:
    proxying_to_dagster(
        global_vars=globals(),
        proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
    )
