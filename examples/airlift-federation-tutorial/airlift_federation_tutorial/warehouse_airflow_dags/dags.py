import os

import duckdb
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airlift_federation_tutorial.constants import (
    CUSTOMERS_COLS,
    CUSTOMERS_CSV_PATH,
    CUSTOMERS_DB_NAME,
    CUSTOMERS_SCHEMA,
    CUSTOMERS_TABLE_NAME,
    DUCKDB_PATH,
)
from dagster._time import get_current_datetime_midnight


def load_customers() -> None:
    # https://github.com/apache/airflow/discussions/24463
    os.environ["NO_PROXY"] = "*"
    df = pd.read_csv(  # noqa: F841 # used by duckdb
        CUSTOMERS_CSV_PATH,
        names=CUSTOMERS_COLS,
    )

    # Connect to DuckDB and create a new table
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {CUSTOMERS_SCHEMA}").fetchall()
    con.execute(
        f"CREATE TABLE IF NOT EXISTS {CUSTOMERS_DB_NAME}.{CUSTOMERS_SCHEMA}.{CUSTOMERS_TABLE_NAME} AS SELECT * FROM df"
    ).fetchall()
    con.close()


with DAG(
    dag_id="load_customers",
    is_paused_upon_creation=False,
    start_date=get_current_datetime_midnight(),
) as dag:
    PythonOperator(
        task_id="load_customers_to_warehouse",
        python_callable=load_customers,
        dag=dag,
    )

# Define some dummy DAGs to simulate a big Airflow instance
for dag_id in ["load_orders", "load_products", "load_payments", "load_sales"]:
    with DAG(
        dag_id=dag_id,
        is_paused_upon_creation=False,
        start_date=get_current_datetime_midnight(),
    ) as dag:
        PythonOperator(
            task_id="task",
            python_callable=lambda: None,
            dag=dag,
        )
    globals()[dag_id] = dag
