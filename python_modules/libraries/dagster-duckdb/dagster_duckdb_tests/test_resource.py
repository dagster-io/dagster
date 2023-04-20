import os

import pandas as pd
from dagster import asset, materialize
from dagster_duckdb import DuckDBResource


def test_resource(tmp_path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": [5, 6, 7]})

    @asset
    def create_table(duckdb: DuckDBResource):
        with duckdb.get_connection() as conn:
            conn.execute("CREATE TABLE my_table AS SELECT * FROM df")

    @asset
    def read_table(duckdb: DuckDBResource):
        with duckdb.get_connection() as conn:
            res = conn.execute("SELECT * FROM my_table").fetchdf()

            assert res.equals(df)

    materialize(
        [create_table, read_table],
        resources={"duckdb": DuckDBResource(database=os.path.join(tmp_path, "unit_test.duckdb"))},
    )
