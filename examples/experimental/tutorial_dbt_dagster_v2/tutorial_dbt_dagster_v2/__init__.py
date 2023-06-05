from dagster import Definitions
from dagster_dbt.cli import DbtCli

from .assets import DBT_PROJECT_DIR
from .assets.build import my_dbt_assets

defs = Definitions(
    assets=[my_dbt_assets],
    resources={
        "dbt": DbtCli(project_dir=DBT_PROJECT_DIR, global_config=["--no-use-colors"]),
    },
)
