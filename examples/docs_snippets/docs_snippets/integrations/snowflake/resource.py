from dagster_snowflake import snowflake_resource

from dagster import Definitions, asset

# this example executes a query against the IRIS_DATASET table created in Step 2 of the
# Using Dagster with Snowflake tutorial


@asset(required_resource_keys={"snowflake"})
def small_petals(context):
    return context.resources.snowflake.execute_query(
        'SELECT * FROM IRIS_DATASET WHERE "Petal length (cm)" < 1 AND "Petal width (cm)" < 1',
        fetch_results=True,
        use_pandas_result=True,
    )


defs = Definitions(
    assets=[small_petals],
    resources={
        "snowflake": snowflake_resource.configured(
            {
                "account": "abc1234.us-east-1",
                "user": {"env": "SNOWFLAKE_USER"},
                "password": {"env": "SNOWFLAKE_PASSWORD"},
                "database": "FLOWERS",
                "schema": "IRIS,",
            }
        )
    },
)
