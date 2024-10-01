from dagster import Definitions, EnvVar, load_assets_from_modules
from dagster_snowflake_pandas import SnowflakePandasIOManager

from .assets import python_and_dbt_assets
from .assets.python_and_dbt_assets import dbt_resource

defs = Definitions(
    assets=load_assets_from_modules(
        modules=[python_and_dbt_assets],
    ),
    resources={
        "io_manager": SnowflakePandasIOManager(
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database=EnvVar("SNOWFLAKE_DATABASE"),
            warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
        ),
        "dbt": dbt_resource,
    },
)
