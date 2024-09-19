from typing import Sequence

import yaml
from dagster_snowflake import SnowflakeResource

import dagster as dg


def build_etl_table(name: str, deps: Sequence[str], query: str) -> dg.Definitions:
    @dg.asset(name=name, deps=deps)
    def etl_table(context, snowflake: SnowflakeResource):
        with snowflake.get_connection() as conn:
            conn.cursor.execute(query)

    return etl_table


def load_etl_tables_from_yaml(yaml_path: str) -> Sequence[dg.AssetsDefinition]:
    config = yaml.safe_load(open(yaml_path))
    factory_assets = [
        build_etl_table(
            name=table_config["name"],
            deps=table_config["deps"],
            query=table_config["query"],
        )
        for table_config in config["etl_tables"]
    ]
    return factory_assets


defs = dg.Definitions(
    assets=load_etl_tables_from_yaml(
        dg.file_relative_path(__file__, "table_definitions.yaml")
    ),
    resources={
        "snowflake": SnowflakeResource(
            user=dg.EnvVar("SNOWFLAKE_USER"),
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
        )
    },
)
