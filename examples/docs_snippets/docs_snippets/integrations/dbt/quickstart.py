# pyright: reportMissingImports=false
# ruff: isort: skip_file

# start_example
from pathlib import Path

from dagster import AssetExecutionContext, Definitions
from dagster_dbt import (
    DbtCliResource,
    DbtProject,
    build_schedule_from_dbt_selection,
    dbt_assets,
)

RELATIVE_PATH_TO_MY_DBT_PROJECT = "./my_dbt_project"

my_project = DbtProject(
    project_dir=Path(__file__)
    .joinpath("..", RELATIVE_PATH_TO_MY_DBT_PROJECT)
    .resolve(),
)


@dbt_assets(manifest=my_project.manifest_path)
def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


my_schedule = build_schedule_from_dbt_selection(
    [my_dbt_assets],
    job_name="materialize_dbt_models",
    cron_schedule="0 0 * * *",
    dbt_select="fqn:*",
)

defs = Definitions(
    assets=[my_dbt_assets],
    schedules=[my_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=my_project),
    },
)
# end_example


def dbt_project_example():
    # start_dbt_project_example
    from pathlib import Path

    from dagster_dbt import DbtProject

    RELATIVE_PATH_TO_MY_DBT_PROJECT = "./my_dbt_project"

    my_project = DbtProject(
        project_dir=Path(__file__)
        .joinpath("..", RELATIVE_PATH_TO_MY_DBT_PROJECT)
        .resolve(),
    )
    # end_dbt_project_example


def dbt_assets_example():
    # start_dbt_assets_example
    from dagster import AssetExecutionContext
    from dagster_dbt import DbtCliResource, dbt_assets

    from .project import my_project

    @dbt_assets(manifest=my_project.manifest_path)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_dbt_assets_example


def dbt_definitions_example():
    # start_dbt_definitions_example
    from dagster import Definitions
    from dagster_dbt import DbtCliResource

    from .assets import my_dbt_assets
    from .project import my_project

    defs = Definitions(
        assets=[
            # your other assets here,
            my_dbt_assets
        ],
        jobs=[
            # your jobs here
        ],
        resources={
            # your other resources here,
            "dbt": DbtCliResource(project_dir=my_project),
        },
    )
    # end_dbt_definitions_example
