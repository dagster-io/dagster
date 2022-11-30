from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import SourceAsset, repository, with_resources

iris_harvest_data = SourceAsset(key="iris_harvest_data")


@repository
def flowers_analysis_repository():
    return with_resources(
        [iris_harvest_data],
        resource_defs={
            "io_manager": snowflake_pandas_io_manager.configured(
                {
                    "database": "FLOWERS",
                    "schema": "IRIS",
                    "account": "abc1234.us-east-1",
                    "user": {"env": "SNOWFLAKE_USER"},
                    "password": {"env": "SNOWFLAKE_PASSWORD"},
                }
            )
        },
    )
