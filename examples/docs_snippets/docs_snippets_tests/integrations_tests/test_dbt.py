from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project

from dagster import file_relative_path, with_resources
from docs_snippets.integrations.dbt.dbt import scope_schedule_assets


def test_scope_schedule_assets_can_load():
    DBT_PROJECT_PATH = file_relative_path(
        __file__, "../../../assets_dbt_python/dbt_project"
    )
    DBT_PROFILES_DIR = file_relative_path(
        __file__,
        "../../../assets_dbt_python/dbt_project/config",
    )
    dbt_assets = with_resources(
        load_assets_from_dbt_project(DBT_PROJECT_PATH),
        {
            "dbt": dbt_cli_resource.configured(
                {"project_dir": DBT_PROJECT_PATH, "profiles_dir": DBT_PROFILES_DIR},
            )
        },
    )

    scope_schedule_assets(dbt_assets)
