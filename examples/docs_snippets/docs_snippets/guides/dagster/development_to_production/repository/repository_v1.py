# start
# __init__.py
from dagster_snowflake import SnowflakeResource

from dagster import Definitions
from development_to_production.assets import comments, items, stories

# Note that storing passwords in configuration is bad practice. It will be resolved later in the guide.
resources = {
    "snowflake_resource": SnowflakeResource(
        account="abc1234.us-east-1",
        user="me@company.com",
        # password in config is bad practice
        password="my_super_secret_password",
        database="LOCAL",
        schema="ALICE",
    ),
}

defs = Definitions(assets=[items, comments, stories], resources=resources)


# end
