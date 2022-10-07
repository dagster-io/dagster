import os
import uuid

import snowflake.connector
from assets_smoke_test import python_and_dbt_assets
from assets_smoke_test.python_and_dbt_assets import raw_country_populations
from dagster_dbt import dbt_cli_resource
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

from dagster import load_assets_from_modules, materialize


def test_smoke_all():
    snowflake_config = {}

    conn = snowflake.connector.connect(**snowflake_config)

    temporary_database_name = "tmp_" + str(uuid.uuid4()).replace("-", "_")

    io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()]).configured(
        {"database": temporary_database_name, **snowflake_config}
    )

    dbt_resource = dbt_cli_resource.configured({"target": "smoke_test"})
    os.environ["SNOWFLAKE_DATABASE"] = temporary_database_name

    conn.execute(f"create database {temporary_database_name}")

    try:
        source_assets = [raw_country_populations]
        for source_asset in source_assets:
            table_name = temporary_database_name + source_asset.key.path[-1]
            columns_str = ", ".join(
                [
                    f"{column.type} {column.name}"
                    for column in source_asset.metadata["column_schema"].columns
                ]
            )
            conn.execute(f"CREATE TABLE {table_name} ({columns_str}")

        assets = load_assets_from_modules([python_and_dbt_assets])

        materialize(assets, resources={"io_manager": io_manager, "dbt": dbt_resource})

    finally:
        conn.execute(f"drop database {temporary_database_name}")
        conn.close()
