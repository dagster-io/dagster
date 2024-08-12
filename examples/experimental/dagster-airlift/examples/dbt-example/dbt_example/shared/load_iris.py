import os

import duckdb
import pandas as pd


def load_csv_to_duckdb() -> None:
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
