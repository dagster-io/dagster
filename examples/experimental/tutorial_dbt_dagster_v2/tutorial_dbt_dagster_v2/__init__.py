from dagster import Definitions
from dagster_dbt import DbtCli

from .assets.build import my_dbt_assets
from .constants import DBT_PROJECT_DIR
from .jobs.yield_materializations import my_dbt_job
from .schedules.define_schedules import daily_dbt_assets_schedule, hourly_staging_dbt_assets

defs = Definitions(
    assets=[my_dbt_assets],
    schedules=[daily_dbt_assets_schedule, hourly_staging_dbt_assets],
    jobs=[my_dbt_job],
    resources={
        "dbt": DbtCli(
            project_dir=DBT_PROJECT_DIR,
            global_config_flags=["--no-use-colors"],
            profile="jaffle_shop",
            target="dev",
        ),
    },
)
