import os

from dagster_dbt import load_assets_from_dbt_project, dbt_cli_resource
from dagster import repository, with_resources
from dagster._utils import file_relative_path

DBT_PROJECT_PATH=file_relative_path(__file__, "../jaffle_shop")
DBT_PROFILES=os.path.expanduser('~') + "/.dbt"

dbt_assets = load_assets_from_dbt_project(project_dir=DBT_PROJECT_PATH, profiles_dir=DBT_PROFILES, key_prefix=["jamie"])


@repository
def jaffle_shop_repository():
    return with_resources(
        dbt_assets,
        {
            "dbt": dbt_cli_resource.configured(
                {"project_dir": DBT_PROJECT_PATH},
            )
        },
    )