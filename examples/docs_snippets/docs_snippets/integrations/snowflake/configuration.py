iris_dataset = None

# start_example

from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import repository, with_resources


@repository
def flowers_analysis_repository():
    return with_resources(
        [iris_dataset],
        resource_defs={
            "io_manager": snowflake_pandas_io_manager.configured(
                {
                    "account": "abc1234.us-east-1",  # required
                    "user": {"env": "SNOWFLAKE_USER"},  # required
                    "password": {"env": "SNOWFLAKE_PASSWORD"},  # required
                    "role": "reader",  # optional, defaults to the default role for the account
                    "warehouse": "PLANTS",  # optional, defaults to default warehouse for the account
                    "database": "FLOWERS",  # required
                    "schema": "IRIS,",  # optional, defaults to PUBLIC
                }
            )
        },
    )


# end_example
