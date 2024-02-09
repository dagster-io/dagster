from dagster import asset


@asset
def iris_dataset():
    return None


# start_example

from dagster_snowflake import SnowflakeResource

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "snowflake": SnowflakeResource(
            account="abc1234.us-east-1",  # required
            user=EnvVar("SNOWFLAKE_USER"),  # required
            password=EnvVar("SNOWFLAKE_PASSWORD"),  # password or private key required
            database="FLOWERS",  # required
            role="writer",  # optional, defaults to the default role for the account
            warehouse="PLANTS",  # optional, defaults to default warehouse for the account
            schema="IRIS",  # optional, defaults to PUBLIC
        )
    },
)


# end_example
