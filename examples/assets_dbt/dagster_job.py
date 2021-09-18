import os

from dagster.core.asset_defs import build_assets_job
from dagster.utils import file_relative_path
from dagster_dbt import dbt_cli_resource
from dagster_dbt.asset_defs import load_assets_from_dbt_project

DBT_PROJECT_DIR = file_relative_path(
    __file__,
    "../../python_modules/libraries/dagster-dbt/dagster_dbt_tests/dagster_dbt_test_project",
)
DBT_PROFILES_DIR = os.path.abspath(file_relative_path(__file__, "./"))

# this list has one element per dbt model
assets = load_assets_from_dbt_project(DBT_PROJECT_DIR, DBT_PROFILES_DIR)

cereals_job = build_assets_job(
    "cereals_job",
    assets,
    resource_defs={
        "dbt": dbt_cli_resource.configured(
            {"profiles-dir": DBT_PROFILES_DIR, "project-dir": DBT_PROJECT_DIR}
        ),
    },
)
