from dataclasses import dataclass

import dagster as dg
import polars as pl
from dagster.components import Component, ComponentLoadContext, Resolvable


@dataclass
class AssetCheckSuite(Component, Resolvable):
    asset: str
    column: str

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        @dg.asset_check(
            asset=self.asset,
            name=f"check_{self.column}_between",
            description="Check that values are within a defined range.",
        )
        def _check(df: pl.DataFrame) -> dg.AssetCheckResult:
            return dg.AssetCheckResult(passed=df[self.target_column].is_between(0, 99).all())

        return dg.Definitions(asset_checks=[_check])
