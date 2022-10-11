import os

import snowflake.connector
from assets_smoke_test import python_and_dbt_assets
from assets_smoke_test.python_and_dbt_assets import (
    DBT_PROFILES_DIR,
    DBT_PROJECT_DIR,
    raw_country_populations,
)
from dagster_dbt import dbt_cli_resource
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

from dagster import load_assets_from_modules, materialize


def smoke_all_test():
    snowflake_config = {
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PASSWORD"],
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
    }

    io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()]).configured(
        snowflake_config
    )

    dbt_resource = dbt_cli_resource.configured(
        {"target": "smoke_test", "project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROFILES_DIR}
    )

    source_assets = [raw_country_populations]

    conn = snowflake.connector.connect(**snowflake_config)

    for source_asset in source_assets:
        db_name = snowflake_config["database"]
        table_name = f"{db_name}.public.{source_asset.key.path[-1]}"
        columns_str = ", ".join(
            [
                f"{column.name} {column.type}"
                for column in source_asset.metadata["column_schema"].schema.columns
            ]
        )
        conn.cursor().execute(f"CREATE OR REPLACE TABLE {table_name} ({columns_str})")

    assets = load_assets_from_modules([python_and_dbt_assets])

    materialize(assets, resources={"io_manager": io_manager, "dbt": dbt_resource})
