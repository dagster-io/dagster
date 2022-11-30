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
                    "warehouse": "PLANTS",
                    "database": "FLOWERS",
                    "schema": "IRIS",
                }
            )
        },
    )


# end_example
