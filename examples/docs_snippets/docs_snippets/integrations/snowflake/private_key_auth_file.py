iris_dataset = None

# start_key_file

from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],  # type: ignore  # (didactic)
    resources={
        "io_manager": snowflake_pandas_io_manager.configured(
            {
                "account": "abc1234.us-east-1",
                "user": {"env": "SNOWFLAKE_USER"},
                "private_key_path": "/path/to/private/key/file.p8",
                "private_key_password": {"env": "SNOWFLAKE_PK_PASSWORD"},
                "database": "FLOWERS",
            }
        )
    },
)

# end_key_file
