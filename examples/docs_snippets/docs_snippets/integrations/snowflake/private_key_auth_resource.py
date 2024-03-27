from dagster import asset


@asset
def iris_dataset():
    return None


# start_direct_key

from dagster_snowflake import SnowflakeResource

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "snowflake": SnowflakeResource(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            private_key=EnvVar("SNOWFLAKE_PK"),
            private_key_password=EnvVar("SNOWFLAKE_PK_PASSWORD"),
            database="FLOWERS",
        )
    },
)

# end_direct_key


# start_key_file

from dagster_snowflake import SnowflakeResource

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "snowflake": SnowflakeResource(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            private_key_path="/path/to/private/key/file.p8",
            private_key_password=EnvVar("SNOWFLAKE_PK_PASSWORD"),
            database="FLOWERS",
        )
    },
)

# end_key_file
