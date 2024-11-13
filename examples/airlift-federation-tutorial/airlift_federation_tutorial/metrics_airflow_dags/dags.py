import os
from datetime import datetime
from typing import Union

import duckdb
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airlift_federation_tutorial.constants import (
    CUSTOMERS_DB_NAME,
    CUSTOMERS_SCHEMA,
    CUSTOMERS_TABLE_NAME,
    DUCKDB_PATH,
    METRICS_SCHEMA,
    METRICS_TABLE_NAME,
)
from dagster._time import get_current_datetime_midnight


def calculate_customer_count() -> None:
    os.environ["NO_PROXY"] = "*"

    con = duckdb.connect(str(DUCKDB_PATH))

    result: Union[tuple, None] = con.execute(
        f"SELECT COUNT(*) FROM {CUSTOMERS_DB_NAME}.{CUSTOMERS_SCHEMA}.{CUSTOMERS_TABLE_NAME}"
    ).fetchone()
    if not result:
        raise ValueError("No customers found")
    count_df = pd.DataFrame([{"date": datetime.now().date(), "total_customers": result[0]}])  # noqa: F841 # used by duckdb

    con.execute(f"CREATE SCHEMA IF NOT EXISTS {METRICS_SCHEMA}").fetchall()

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS {CUSTOMERS_DB_NAME}.{METRICS_SCHEMA}.{METRICS_TABLE_NAME} (
            date DATE,
            total_customers INTEGER
        )
    """).fetchall()

    con.execute(
        f"INSERT INTO {CUSTOMERS_DB_NAME}.{METRICS_SCHEMA}.{METRICS_TABLE_NAME} SELECT * FROM count_df"
    ).fetchall()

    con.close()


with DAG(
    dag_id="customer_metrics",
    is_paused_upon_creation=False,
    start_date=get_current_datetime_midnight(),
) as dag:
    count_task = PythonOperator(
        task_id="calculate_customer_count",
        python_callable=calculate_customer_count,
        dag=dag,
    )

for dag_id in ["orders_metrics", "products_metrics", "payments_metrics", "sales_metrics"]:
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
