# pyright: reportMissingImports=false
# ruff: isort: skip_file

# start_dbt_project_example
from pathlib import Path

from dagster_dbt import DbtProject

RELATIVE_PATH_TO_MY_DBT_PROJECT = "./my_dbt_project"

my_project = DbtProject(
    project_dir=Path(__file__)
    .joinpath("..", RELATIVE_PATH_TO_MY_DBT_PROJECT)
    .resolve(),
)
my_project.prepare_if_dev()
# end_dbt_project_example


# fmt: off
# start_dbt_assets_example
from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from .project import my_project

@dbt_assets(manifest=my_project.manifest_path)
def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
# end_dbt_assets_example
# fmt: on


# start_dbt_definitions_example
from dagster import Definitions
from dagster_dbt import DbtCliResource

from .assets import my_dbt_assets
from .project import my_project

defs = Definitions(
    ...,
    assets=[  # type: ignore
        ...,
        # Add the dbt assets alongside your other asset
        my_dbt_assets,
    ],
    resources={
        ...: ...,
        # Add the dbt resource alongside your other resources
        "dbt": DbtCliResource(project_dir=my_project),
    },
)
# end_dbt_definitions_example
