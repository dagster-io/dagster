from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

from dagster import repository, with_resources

from ..assets import comments, items, stories

# the snowflake io manager can be initialized to handle different data types
# here we use the pandas type handler so we can store pandas DataFrames
snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

# start
# repository.py


@repository
def repo():
    resource_defs = {
        "io_manager": snowflake_io_manager.configured(
            {
                "account": "abc1234.us-east-1",
                "user": "me@company.com",
                # storing passwords in configuration is bad practice. We'll address this later
                # in the guide
                "password": "my_super_secret_password",
                "database": "LOCAL",
                "schema": "ALICE",
            }
        ),
    }

    return [*with_resources([items, comments, stories], resource_defs=resource_defs)]


# end
