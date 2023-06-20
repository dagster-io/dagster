from dagster import Definitions
from dagster_dbt.cli import DbtCli

from .assets.build import my_dbt_assets
from .constants import DBT_PROJECT_DIR
from .jobs.yield_materializations import my_dbt_job

defs = Definitions(
    assets=[my_dbt_assets],
    jobs=[my_dbt_job],
    resources={
        "dbt": DbtCli(
            project_dir=DBT_PROJECT_DIR,
            global_config=["--no-use-colors"],
            profile="jaffle_shop",
            target="dev",
        ),
    },
)
