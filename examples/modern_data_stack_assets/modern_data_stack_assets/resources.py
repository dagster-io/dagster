from dagster_airbyte import airbyte_resource
from dagster_dbt import dbt_cli_resource

from .constants import AIRBYTE_CONFIG, DBT_CONFIG, POSTGRES_CONFIG
from .db_io_manager import db_io_manager

resource_defs = {
    "airbyte": airbyte_resource.configured(AIRBYTE_CONFIG),
    "dbt": dbt_cli_resource.configured(DBT_CONFIG),
    "db_io_manager": db_io_manager.configured(POSTGRES_CONFIG),
}
