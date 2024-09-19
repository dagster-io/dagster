import os

from dagster_snowflake_pandas import SnowflakePandasIOManager

from dagster import Definitions
from development_to_production.assets.hacker_news_assets import comments, items, stories

# start
# definitions.py

# Note that storing passwords in configuration is bad practice. It will be resolved soon.
resources = {
    "local": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user="me@company.com",
            # password in config is bad practice
            password="my_super_secret_password",
            database="LOCAL",
            schema="ALICE",
        ),
    },
    "production": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user="dev@company.com",
            # password in config is bad practice
            password="company_super_secret_password",
            database="PRODUCTION",
            schema="HACKER_NEWS",
        ),
    },
}
deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")

defs = Definitions(
    assets=[items, comments, stories], resources=resources[deployment_name]
)


# end
