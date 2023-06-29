import os

from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCli
from dagster_duckdb_pandas import DuckDBPandasIOManager

from tutorial_dbt_dagster import assets
from tutorial_dbt_dagster.assets import DBT_PROJECT_PATH

resources = {
    "dbt": DbtCli(project_dir=DBT_PROJECT_PATH),
    "io_manager": DuckDBPandasIOManager(database=os.path.join(DBT_PROJECT_PATH, "tutorial.duckdb")),
}

defs = Definitions(assets=load_assets_from_modules([assets]), resources=resources)
