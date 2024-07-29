import os
from datetime import datetime

import duckdb
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator


def load_csv_to_duckdb():
    # Absolute path to the iris dataset is path to current file's directory
    csv_path = os.path.join(os.path.dirname(__file__), "iris.csv")
    # Duckdb database stored in airflow home
    duckdb_path = os.path.join(os.environ["AIRFLOW_HOME"], "jaffle_shop.duckdb")
    iris_df = pd.read_csv(  # noqa: F841 # used by duckdb
        csv_path,
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )

    # Connect to DuckDB and create a new table
    con = duckdb.connect(duckdb_path)
    con.execute("CREATE SCHEMA IF NOT EXISTS iris_dataset").fetchall()
    con.execute(
        "CREATE TABLE IF NOT EXISTS jaffle_shop.iris_dataset.iris_lakehouse_table AS SELECT * FROM iris_df"
    ).fetchall()
    con.close()


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

dag = DAG("load_lakehouse", default_args=default_args, schedule_interval=None)
load_iris = PythonOperator(task_id="load_iris", python_callable=load_csv_to_duckdb, dag=dag)
