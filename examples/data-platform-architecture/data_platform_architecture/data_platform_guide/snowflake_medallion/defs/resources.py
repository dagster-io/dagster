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
            return pd.DataFrame()
        return pd.DataFrame()


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
