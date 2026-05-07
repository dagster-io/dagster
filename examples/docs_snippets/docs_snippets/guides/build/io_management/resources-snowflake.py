from dagster_snowflake_pandas import SnowflakePandasIOManager

import dagster as dg


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            # highlight-start
            # Swap in a Snowflake I/O manager
            "io_manager": SnowflakePandasIOManager(
                database=dg.EnvVar("SNOWFLAKE_DATABASE"),
                account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
                user=dg.EnvVar("SNOWFLAKE_USER"),
                password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            )
            # highlight-end
        }
    )
