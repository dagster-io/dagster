from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import dagster as dg
import pandas as pd
from dagster_components import (
    AssetSpecModel,
    Component,
    ComponentLoadContext,
    ResolutionContext,
    ResolvableModel,
    ResolvedFrom,
)
from dagster_components.resolved.core_models import ResolvedAssetSpec
from sqlalchemy import create_engine


# start_sql_component_model
class SqlComponentModel(ResolvableModel):
    sql_path: str
    sql_engine_url: str
    asset_specs: Sequence[AssetSpecModel]


# end_sql_component_model


def resolve_asset_specs(
    context: ResolutionContext, schema: SqlComponentModel
) -> Sequence[dg.AssetSpec]:
    return context.resolve_value(schema.asset_specs)


# start_sql_component_class
@dataclass
class SqlComponent(Component, ResolvedFrom[SqlComponentModel]):
    """A component that allows you to write SQL without learning dbt or Dagster's concepts."""

    sql_path: str
    sql_engine_url: str
    asset_specs: Sequence[ResolvedAssetSpec]

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions:
        resolved_sql_path = Path(load_context.path, self.sql_path).absolute()

        @dg.multi_asset(name=Path(self.sql_path).stem, specs=self.asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            return self.execute(context, resolved_sql_path)

        return dg.Definitions(assets=[_asset])

    # end_sql_component_class

    # start_execute_method
    def execute(self, context: dg.AssetExecutionContext, resolved_sql_path: Path):
        with open(resolved_sql_path) as f:
            query = f.read()

        engine = create_engine(self.sql_engine_url)

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        return dg.MaterializeResult(
            metadata={
                "query": dg.MetadataValue.md(query),
                "df": dg.MetadataValue.md(df.head().to_markdown()),
            },
        )

    # end_execute_method
