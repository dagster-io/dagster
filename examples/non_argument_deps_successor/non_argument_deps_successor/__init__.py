from dagster import Definitions, load_assets_from_modules

from . import assets
from .assets import DBT_PROFILES_DIR, DBT_PROJECT_DIR
from dagster_dbt import DbtCliClientResource
from dagster_dbt.cli import DbtCli

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
    resources={
        "dbt": DbtCli(
            project_dir=DBT_PROJECT_DIR,
            # profiles_dir=DBT_PROFILES_DIR,
        ),
    },
)
