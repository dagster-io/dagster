# start
# repository.py
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

from dagster import repository, with_resources

from local_to_production.assets import comments, items, stories

snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])


# Note that storing passwords in configuration is bad practice. It will be resolved later in the guide.
@repository
def repo():
    resource_defs = {
        "snowflake_io_manager": snowflake_io_manager.configured(
            {
                "account": "abc1234.us-east-1",
                "user": "me@company.com",
                # password in config is bad practice
                "password": "my_super_secret_password",
                "database": "LOCAL",
                "schema": "ALICE",
            }
        ),
    }

    return [*with_resources([items, comments, stories], resource_defs=resource_defs)]


# end
