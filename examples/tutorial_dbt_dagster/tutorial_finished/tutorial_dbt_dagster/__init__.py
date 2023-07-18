import os

from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCliClient
from dagster_duckdb import DuckDBResource

from tutorial_dbt_dagster import assets
from tutorial_dbt_dagster.assets import DBT_PROJECT_PATH

resources = {
    "dbt": DbtCliClient(project_dir=DBT_PROJECT_PATH),
    "duckdb": DuckDBResource(database=os.path.join(DBT_PROJECT_PATH, "tutorial.duckdb")),
}

defs = Definitions(assets=load_assets_from_modules([assets]), resources=resources)
