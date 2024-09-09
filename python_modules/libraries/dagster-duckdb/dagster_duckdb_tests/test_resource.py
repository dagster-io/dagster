import os

import pandas as pd
import pytest
from dagster import asset, job, materialize, op
from dagster_duckdb import DuckDBResource


def test_resource(tmp_path):
    sample_df = pd.DataFrame({"a": [1, 2, 3], "b": [5, 6, 7]})

    @asset
    def create_table(duckdb: DuckDBResource):
        my_df = sample_df  # noqa: F841
        with duckdb.get_connection() as conn:
            conn.execute("CREATE TABLE my_table AS SELECT * FROM my_df")

    @asset
    def read_table(duckdb: DuckDBResource):
        with duckdb.get_connection() as conn:
            res = conn.execute("SELECT * FROM my_table").fetchdf()

            assert res.equals(sample_df)

    materialize(
        [create_table, read_table],
        resources={"duckdb": DuckDBResource(database=os.path.join(tmp_path, "unit_test.duckdb"))},
    )


@pytest.mark.parametrize(
    "connection_config",
    [{"arrow_large_buffer_size": False}, {"arrow_large_buffer_size": True}],
)
def test_config(tmp_path, connection_config):
    @op(required_resource_keys={"duckdb"})
    def check_config_op(context):
        with context.resources.duckdb.get_connection() as conn:
            for name, value in connection_config.items():
                res = conn.execute(f"SELECT current_setting('{name}')").fetchone()

                assert res[0] == value

    @job(
        resource_defs={
            "duckdb": DuckDBResource(
                database=os.path.join(tmp_path, "unit_test.duckdb"),
                connection_config=connection_config,
            )
        }
    )
    def check_config_job():
        check_config_op()

    assert check_config_job.execute_in_process().success
