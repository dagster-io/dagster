import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import dagster as dg
import duckdb
from dagster_components import (
    AssetSpecModel,
    Component,
    ComponentLoadContext,
    ResolvableModel,
    ResolvedFrom,
)
from dagster_components.resolved.core_models import ResolvedAssetSpec


class DuckDbComponentModel(ResolvableModel):
    sql_file: str
    assets: Sequence[AssetSpecModel]


@dataclass
class DuckDbComponent(Component, ResolvedFrom[DuckDbComponentModel]):
    """A component that allows you to write SQL without learning dbt or Dagster's concepts."""

    assets: Sequence[ResolvedAssetSpec]
    sql_file: str

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:  # pyright: ignore[reportIncompatibleMethodOverride]
        assert len(self.assets) >= 1, "Must have asset"
        name = f"run_{self.assets[0].key.to_user_string()}"
        path = (load_context.path / Path(self.sql_file)).absolute()
        # assert path.exists(), f"Path {path} does not exist."

        @dg.multi_asset(name=name, specs=self.assets)
        def _asset(context: dg.AssetExecutionContext):
            return self.execute(context, str(path))

        return dg.Definitions(assets=[_asset])

    def execute(self, context: dg.AssetExecutionContext, sql_file: str):
        # Connect to DuckDB
        con = duckdb.connect()

        # Original working directory (to restore later)
        original_dir = os.getcwd()
        try:
            os.chdir(Path(__file__).parent)
            query = open(sql_file).read()
            # query = f"SELECT * FROM '{csv_path}'"
            # Read CSV from parent directory
            df = con.execute(query).fetchdf()
        finally:
            os.chdir(original_dir)

        md = df.head().to_markdown(index=False)
        print(md)  # noqa
        for spec in self.assets:
            yield dg.MaterializeResult(
                asset_key=spec.key,
                metadata={
                    "query": dg.MetadataValue.md(query),
                    "df": dg.MetadataValue.md(md),
                },
            )
