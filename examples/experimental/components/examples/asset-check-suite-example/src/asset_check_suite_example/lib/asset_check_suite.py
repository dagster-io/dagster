from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Union

import dagster as dg
import polars as pl
from dagster.components import Component, ComponentLoadContext, Resolvable
from pydantic import BaseModel


class BaseCheck(BaseModel):
    columns: list[str]


class CheckIsBetween(BaseCheck):
    type: Literal["is_between"]
    min: int
    max: int

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return dg.AssetCheckResult(passed=df[column].is_between(self.min, self.max).all())


class CheckIsNotNull(BaseCheck):
    type: Literal["is_not_null"]

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return df[column].is_null().not_().all()


@dataclass
class AssetCheckSuite(Component, Resolvable):
    asset: str
    checks: Sequence[Union[CheckIsBetween, CheckIsNotNull]]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        def _build_checks():
            for check in self.checks:
                for column in check.columns:

                    @dg.asset_check(
                        asset=self.asset,
                        name=f"check_{column}_{check.type}",
                        description="Check that values are within a defined range.",
                    )
                    def _check(df: pl.DataFrame) -> dg.AssetCheckResult:
                        return dg.AssetCheckresult(passed=check.check(df, column))

                    yield _check

        return dg.Definitions(asset_checks=list(_build_checks()))
