import os
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import dagster as dg
import duckdb
from dagster_components import (
    Component,
    ComponentLoadContext,
    Model,
    Resolvable,
    Scaffolder,
    ScaffoldRequest,
    scaffold_component,
)
from dagster_components.resolved.core_models import ResolvedAssetSpec
from dagster_components.scaffold.scaffold import scaffold_with
from pydantic import BaseModel


class DuckDbScaffolderParams(BaseModel):
    sql_file: Optional[str]
    asset_key: Optional[str]


class DuckDbComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: DuckDbScaffolderParams) -> None:
        root_name = request.target_path.stem
        asset_key = params.asset_key or f"{root_name}"
        sql_file = params.sql_file or f"{root_name}.sql"

        Path(sql_file).touch()

        scaffold_component(
            request=request,
            yaml_attributes={"sql_file": sql_file, "assets": [{"key": asset_key}]},
        )


@scaffold_with(DuckDbComponentScaffolder)
class DuckDbComponent(Component, Model, Resolvable):
    """A component that allows you to write SQL without learning dbt or Dagster's concepts."""

    assets: Sequence[ResolvedAssetSpec]
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
