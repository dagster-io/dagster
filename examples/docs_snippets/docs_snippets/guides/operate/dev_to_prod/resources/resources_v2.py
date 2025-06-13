# highlight-start
import os
# highlight-end

import dagster as dg

from dagster_snowflake_pandas import SnowflakePandasIOManager

# Note that storing passwords in configuration is bad practice. It will be resolved soon.
@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources = {
            # highlight-start
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
            # highlight-end
        }
    )

# highlight-start
deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")

defs = dg.Definitions(
    resources=resources[deployment_name]
)
# highlight-end
