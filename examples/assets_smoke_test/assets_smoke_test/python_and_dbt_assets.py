from dagster import (
    Definitions,
    EnvVar,
    SourceAsset,
    TableSchema,
    asset,
    load_assets_from_current_module,
)
from dagster._utils import file_relative_path
from dagster_dbt import DbtCli, load_assets_from_dbt_project
from dagster_snowflake_pandas import SnowflakePandasIOManager
from pandas import DataFrame

DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_project")

raw_country_populations = SourceAsset(
    "raw_country_populations",
    metadata={
        "column_schema": TableSchema.from_name_type_dict(
            {
                "country": "string",
                "continent": "string",
                "region": "string",
                "pop2018": "int",
                "pop2019": "int",
                "change": "string",
            }
        ),
    },
)


@asset
def country_stats(country_populations: DataFrame, continent_stats: DataFrame) -> DataFrame:
    result = country_populations.join(continent_stats, on="continent", lsuffix="_continent")
    result["continent_pop_fraction"] = result["pop2019"] / result["pop2019_continent"]
    return result


dbt_assets = load_assets_from_dbt_project(DBT_PROJECT_DIR)


defs = Definitions(
    assets=load_assets_from_current_module(),
    resources={
        "io_manager": SnowflakePandasIOManager(
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database=EnvVar("SNOWFLAKE_DATABASE"),
            warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
        ),
        "dbt": DbtCli(project_dir=DBT_PROJECT_DIR),
    },
)
