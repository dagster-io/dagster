import dagster as dg

from dagster_snowflake_pandas import SnowflakePandasIOManager


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        # Note that storing passwords in configuration is bad practice. It will be resolved later in the guide.
        resources={
            "snowflake_io_manager": SnowflakePandasIOManager(
                account="abc1234.us-east-1",
                user="me@company.com",
                # password in config is bad practice
                password="my_super_secret_password",
                database="LOCAL",
                schema="ALICE",
            ),
        }
    )
