from pathlib import Path

import dagster as dg
import duckdb
from dagster_components import Component, ComponentLoadContext, Model, Resolvable


class DuckDbComponent(Component, Model, Resolvable):
    """A component that allows you to write SQL without learning dbt or Dagster's concepts."""

    csv_path: str
    asset_key: str

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        name = f"run_{self.asset_key}"
        asset_specs = [dg.AssetSpec(key=self.asset_key)]
        path = (context.path / Path(self.csv_path)).absolute()
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
