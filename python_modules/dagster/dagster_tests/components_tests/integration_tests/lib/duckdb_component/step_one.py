# curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv

from dataclasses import dataclass
from pathlib import Path

import dagster as dg
import duckdb
from dagster.components import Component, ComponentLoadContext


@dataclass
class DuckDbComponent(Component):
    """A component that allows you to write SQL without learning dbt or Dagster's concepts."""

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        name = "op_name"
        asset_specs = [dg.AssetSpec(key="the_key")]
        path = (context.path / Path("raw_customers.csv")).absolute()
        assert path.exists(), f"Path {path} does not exist."

        @dg.multi_asset(name=name, specs=asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            return self.execute(context, str(path))

        return dg.Definitions(assets=[_asset])

    def execute(self, context: dg.AssetExecutionContext, csv_path: str):
        # Connect to DuckDB
        con = duckdb.connect()

        query = f"SELECT * FROM '{csv_path}'"
        # Read CSV from parent directory
        df = con.execute(query).fetchdf()

        md = df.head().to_markdown(index=False)
        print(md)  # noqa
        return dg.MaterializeResult(
            metadata={
                "query": dg.MetadataValue.md(query),
                "df": dg.MetadataValue.md(md),
            },
        )
