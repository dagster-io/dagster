from dagster import Definitions
from dagster_dbt.cli import DbtCli

from tutorial_dbt_dagster_v2.assets import DBT_PROJECT_DIR
from tutorial_dbt_dagster_v2.assets.build import my_dbt_assets

defs = Definitions(
    assets=[my_dbt_assets],
    resources={
        "dbt": DbtCli(project_dir=DBT_PROJECT_DIR, global_config=["--no-use-colors"]),
    },
)
