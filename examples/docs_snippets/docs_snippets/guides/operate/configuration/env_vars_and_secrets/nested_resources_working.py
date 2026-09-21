import os

from dagster_duckdb import DuckDBResource
from dagster_snowflake import SnowflakeResource

import dagster as dg


# highlight-start
class DynamicDatabaseResource(dg.ConfigurableResource):
    env: str
    snowflake: SnowflakeResource
    duckdb: DuckDBResource

    def get_resource(self) -> dg.ConfigurableResource:
        if self.env == "production":
            return self.snowflake
        else:
            return self.duckdb


# highlight-end


@dg.definitions
def defs() -> dg.Definitions:
    return dg.Definitions(
        resources={
            # highlight-start
            "database": DynamicDatabaseResource(
                env=os.getenv("DAGSTER_ENV", "development"),
                snowflake=SnowflakeResource(
                    account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
                    user=dg.EnvVar("SNOWFLAKE_USER"),
                    password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
                    warehouse=dg.EnvVar("SNOWFLAKE_WAREHOUSE"),
                    database=dg.EnvVar("SNOWFLAKE_DATABASE"),
                    schema=dg.EnvVar("SNOWFLAKE_SCHEMA"),
                ),
                duckdb=DuckDBResource(database=dg.EnvVar("DUCKDB_DATABASE")),
            ),
            # highlight-end
        },
    )
