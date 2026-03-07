import os
from collections.abc import Sequence
from pathlib import Path

import dagster as dg
import duckdb
from dagster import ComponentLoadContext
from pydantic import BaseModel


class DuckDbScaffolderParams(BaseModel):
    sql_file: str | None
    asset_key: str | None


class DuckDbComponentScaffolder(dg.Scaffolder[DuckDbScaffolderParams]):
    def scaffold(self, request: dg.ScaffoldRequest[DuckDbScaffolderParams]) -> None:
        root_name = request.target_path.stem
        asset_key = request.params.asset_key or f"{root_name}"
        sql_file = request.params.sql_file or f"{root_name}.sql"

        Path(sql_file).touch()

        dg.scaffold_component(
            request=request,
            yaml_attributes={"sql_file": sql_file, "assets": [{"key": asset_key}]},
        )


@dg.scaffold_with(DuckDbComponentScaffolder)
class DuckDbComponent(dg.Component, dg.Model, dg.Resolvable):
    """A component that allows you to write SQL without learning dbt or Dagster's concepts."""

    assets: Sequence[dg.ResolvedAssetSpec]
    sql_file: str

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        assert len(self.assets) >= 1, "Must have asset"
        name = f"run_{self.assets[0].key.to_user_string()}"
        sql_file_path = (context.path / Path(self.sql_file)).absolute()
        assert sql_file_path.exists(), f"Path {sql_file_path} does not exist."

        @dg.multi_asset(name=name, specs=self.assets)
        def _asset(context: dg.AssetExecutionContext):
            return self.execute(context, str(sql_file_path))

        return dg.Definitions(assets=[_asset])

    def execute(self, context: dg.AssetExecutionContext, sql_file: str):
        # Connect to DuckDB
        con = duckdb.connect()

        # Original working directory (to restore later)
        original_dir = os.getcwd()
        try:
            os.chdir(Path(__file__).parent)
            query = open(sql_file).read()
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
