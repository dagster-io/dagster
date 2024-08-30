from typing import Sequence

import dagster as dg


def build_etl_table(name: str, deps: Sequence[str], query: str) -> dg.Definitions: ...


def load_etl_tables_from_yaml(yaml_path: str) -> Sequence[dg.AssetsDefinition]: ...


etl_tables = load_etl_tables_from_yaml("table_definitions.yaml")


@dg.asset(deps=[etl_table.key for etl_table in etl_tables])
def aggregated_metrics(): ...


defs = dg.Definitions(assets=[*etl_tables, aggregated_metrics])
