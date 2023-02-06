iris_dataset = None

# start_configuration

from dagster_snowflake_pyspark import snowflake_pyspark_io_manager

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": snowflake_pyspark_io_manager.configured(
            {
                "account": "abc1234.us-east-1",  # required
                "user": {"env": "SNOWFLAKE_USER"},  # required
                "password": {"env": "SNOWFLAKE_PASSWORD"},  # required
                "database": "FLOWERS",  # required
                "warehouse": "PLANTS",  # required for pyspark
                "role": "writer",  # optional, defaults to the default role for the account
                "schema": "IRIS",  # optional, defaults to PUBLIC
            }
        )
    },
)

# end_configuration
