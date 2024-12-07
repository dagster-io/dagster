# start_dbt_project_assets
import os
from pathlib import Path

from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets


def dbt_project_path() -> Path:
    env_val = os.getenv("TUTORIAL_DBT_PROJECT_DIR")
    assert env_val, "TUTORIAL_DBT_PROJECT_DIR must be set"
    return Path(env_val)


@dbt_assets(
    manifest=dbt_project_path() / "target" / "manifest.json",
    project=DbtProject(dbt_project_path()),
)
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# end_dbt_project_assets

# start_mapping
from dagster_airlift.core import assets_with_task_mappings

mapped_assets = assets_with_task_mappings(
    dag_id="rebuild_customers_list",
    task_mappings={
        "build_dbt_models":
        # load rich set of assets from dbt project
        [dbt_project_assets],
    },
)
# end_mapping

# start_defs
from dagster import Definitions

defs = Definitions(
    assets=mapped_assets, resources={"dbt": DbtCliResource(project_dir=dbt_project_path())}
)
# end_defs
