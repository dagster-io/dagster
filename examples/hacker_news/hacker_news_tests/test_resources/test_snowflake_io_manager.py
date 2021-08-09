import os
import uuid
from contextlib import contextmanager

from dagster import build_init_resource_context, build_input_context, build_output_context
from hacker_news.resources.snowflake_io_manager import connect_snowflake, snowflake_io_manager
from pandas import DataFrame


def generate_snowflake_config():
    return {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "database": "DEMO_DB",
        "warehouse": "TINY_WAREHOUSE",
    }


@contextmanager
def temporary_snowflake_table(contents: DataFrame):
    snowflake_config = generate_snowflake_config()
    table_name = "a" + str(uuid.uuid4()).replace("-", "_")
    with connect_snowflake(snowflake_config) as con:
        contents.to_sql(name=table_name, con=con, index=False, schema="public")
    try:
        yield table_name
    finally:
        with connect_snowflake(snowflake_config) as conn:
            conn.execute(f"drop table public.{table_name}")


def test_handle_output_then_load_input():
    snowflake_config = generate_snowflake_config()
    snowflake_manager = snowflake_io_manager(build_init_resource_context(config=snowflake_config))
    contents1 = DataFrame([{"col1": "a", "col2": 1}])  # just to get the types right
    contents2 = DataFrame([{"col1": "b", "col2": 2}])  # contents we will insert
    with temporary_snowflake_table(contents1) as temp_table_name:
        metadata = {
            "table": f"public.{temp_table_name}",
        }
        output_context = build_output_context(metadata=metadata, resource_config=snowflake_config)

        list(snowflake_manager.handle_output(output_context, contents2))  # exhaust the iterator

        input_context = build_input_context(
            upstream_output=output_context, resource_config=snowflake_config
        )
        input_value = snowflake_manager.load_input(input_context)
        assert input_value.equals(contents2), f"{input_value}\n\n{contents2}"
