from dagster import repository, with_resources
from ..resources.resources_v1 import hn_api_client
from ..assets import comments, items, stories
from dagster_snowflake import build_snowflake_io_manager, snowflake_resource
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
import os
from .clone_and_drop_db import clone_prod

snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

snowflake_config = {
    "account": {"env": "SNOWFLAKE_ACCOUNT"},
    "user": {"env": "SNOWFLAKE_USER"},
    "password": {"env": "SNOWFLAKE_PASSWORD"},
    "schema": {"env": "SNOWFLAKE_SCHEMA"},
}

# start_resources
resource_defs = {
    "branch": {
        "hn_client": hn_api_client,
        "snowflake_io_mgr": snowflake_io_manager.configured(
            {
                **snowflake_config,
                "database": f"PRODUCTION_CLONE_{os.getenv('DAGSTER_CLOUD_PULL_REQUEST_ID')}",
            }
        ),
        "snowflake": snowflake_resource.configured(
            {
                **snowflake_config,
                "database": f"PRODUCTION_CLONE_{os.getenv('DAGSTER_CLOUD_PULL_REQUEST_ID')}",
            }
        ),
    },
    "production": {
        "hn_client": hn_api_client,
        "snowflake_io_mgr": snowflake_io_manager.configured(
            {
                **snowflake_config,
                "database": "PRODUCTION",
            }
        ),
        "snowflake": snowflake_resource.configured({**snowflake_config, "database": "PRODUCTION"}),
    },
}
# end_resources


def get_current_env():
    is_branch_depl = os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT")
    assert is_branch_depl != None  # env var must be set
    return "branch" if is_branch_depl else "prod"


# start_repository
@repository
def repo():
    ...
    return [
        with_resources([items, comments, stories], resource_defs=resource_defs[get_current_env()]),
        clone_prod.to_job(resource_defs=resource_defs[get_current_env()]),
    ]


# end_repository
