from dagster import Definitions
from dagster_dbt.cli.resources_v2 import DbtClientV2

from tutorial_dbt_dagster_v2.assets import DBT_PROJECT_DIR
from tutorial_dbt_dagster_v2.assets.dbt_customize_asset_metadata import dbt_assets

defs = Definitions(
    assets=[dbt_assets],
    resources={
        "dbt": DbtClientV2(project_dir=DBT_PROJECT_DIR, global_config=["--no-use-colors"]),
    },
)
