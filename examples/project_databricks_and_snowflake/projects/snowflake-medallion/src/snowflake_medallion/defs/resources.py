import os
from pathlib import Path

import pandas as pd
from dagster import ConfigurableResource
from dagster_dbt import DbtCliResource


class SnowflakeResource(ConfigurableResource):
    account: str = ""
    user: str = ""
    password: str = ""
    warehouse: str = ""
    database: str = ""
    db_schema: str = "PUBLIC"
    demo_mode: bool = False

    def query(self, sql: str) -> pd.DataFrame:
        if self.demo_mode:
            return pd.DataFrame({"result": ["demo_query_result"]})
        raise NotImplementedError(
            "Real Snowflake connection not implemented in this example. "
            "Set SNOWFLAKE_ACCOUNT to use demo mode."
        )


def create_dbt_resource(demo_mode: bool = False) -> DbtCliResource:
    project_dir = Path(__file__).parent.parent / "dbt_project"

    if demo_mode:
        return DbtCliResource(
            project_dir=project_dir,
            profiles_dir=project_dir,
            target="duckdb",
        )
    else:
        return DbtCliResource(
            project_dir=project_dir,
            profiles_dir=project_dir,
            target="snowflake",
        )


snowflake_resource = SnowflakeResource(
    account=os.getenv("SNOWFLAKE_ACCOUNT", ""),
    user=os.getenv("SNOWFLAKE_USER", ""),
    password=os.getenv("SNOWFLAKE_PASSWORD", ""),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", ""),
    database=os.getenv("SNOWFLAKE_DATABASE", ""),
    db_schema=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
    demo_mode=not bool(os.getenv("SNOWFLAKE_ACCOUNT")),
)

dbt_resource = create_dbt_resource(demo_mode=not bool(os.getenv("SNOWFLAKE_ACCOUNT")))
