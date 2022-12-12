from dagster import asset


@asset
def iris_dataset():
    return None


# start_example

from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": snowflake_pandas_io_manager.configured(
            {
                "account": "abc1234.us-east-1",  # required
                "user": {"env": "SNOWFLAKE_USER"},  # required
                "password": {"env": "SNOWFLAKE_PASSWORD"},  # required
                "database": "FLOWERS",  # required
                "role": "writer",  # optional, defaults to the default role for the account
                "warehouse": "PLANTS",  # optional, defaults to default warehouse for the account
                "schema": "IRIS,",  # optional, defaults to PUBLIC
            }
        )
    },
)


# end_example
