from dagster import asset


@asset
def iris_dataset():
    return None


# start_configuration

from dagster_snowflake_pyspark import SnowflakePySparkIOManager

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": SnowflakePySparkIOManager(
            account="abc1234.us-east-1",  # required
            user=EnvVar("SNOWFLAKE_USER"),  # required
            password=EnvVar("SNOWFLAKE_PASSWORD"),  # password or private key required
            database="FLOWERS",  # required
            warehouse="PLANTS",  # required for PySpark
            role="writer",  # optional, defaults to the default role for the account
            schema="IRIS",  # optional, defaults to PUBLIC
        )
    },
)

# end_configuration
