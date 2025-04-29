from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, Union

import dagster as dg
import polars as pl
from dagster.components import Component, ComponentLoadContext, Resolvable
from pydantic import BaseModel

from asset_check_suite_example.lib.patterns import REGEX_PATTERNS, PatternType


class BaseCheck(BaseModel):
    columns: list[str]
    description: str


class CheckIsBetween(BaseCheck):
    type: Literal["is_between"]
    description: str = "Check that values are within a defined range"
    min: int
    max: int

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return df[column].is_between(self.min, self.max).all()


class CheckIsNotNull(BaseCheck):
    type: Literal["is_not_null"]
    description: str = "Check that the column has no null values"

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return df[column].is_null().not_().all()


class CheckHasUniqueValues(BaseCheck):
    type: Literal["has_unique_values"]
    description: str = "Check that all values in the column are unique"

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return df[column].is_unique().all()


class CheckMatchesRegex(BaseCheck):
    type: Literal["matches_regex"]
    pattern: str
    description: str = "Check that all string values match a specific pattern"

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return df[column].str.contains(self.pattern).all()


class CheckMatchesPattern(BaseCheck):
    type: Literal["matches_pattern"]
    pattern: PatternType
    description: str = "Check that all strings match the predefined `pattern`"

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return df[column].str.contains(REGEX_PATTERNS[self.pattern]).all()


class CheckIsInSet(BaseCheck):
    type: Literal["is_in_set"]
    valid_values: list[Any]
    description: str = "Check that all values are within a predefined set of values"

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return df[column].is_in(self.valid_values).all()


class CheckHasExpectedLength(BaseCheck):
    type: Literal["has_expected_length"]
    length: int
    description: str = "Check that string values have an expected length"

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return (df[column].str.len_chars() == self.length).all()


class CheckContainsSubstring(BaseCheck):
    type: Literal["contains_substring"]
    substring: str
    description: str = "Check that all strings contain a specific substring"

    def check(self, df: pl.DataFrame, column: str) -> bool:
        return df[column].str.contains(self.substring).all()


@dataclass
class AssetCheckSuite(Component, Resolvable):
    asset: str
    checks: Sequence[
        Union[
            CheckIsBetween,
            CheckIsNotNull,
            CheckHasUniqueValues,
            CheckMatchesRegex,
            CheckIsInSet,
            CheckHasExpectedLength,
            CheckContainsSubstring,
            CheckMatchesPattern,
        ]
    ]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        def _build_checks():
            for check in self.checks:
                for column in check.columns:

                    @dg.asset_check(
                        asset=self.asset,
                        name=f"check_{column}_{check.type}",
                        description=check.description,
                    )
                    def _check(df: pl.DataFrame) -> dg.AssetCheckResult:
                        # TODO: do not pass column, use `columns` in check itself
                        return dg.AssetCheckResult(passed=check.check(df, column))

                    yield _check

        return dg.Definitions(asset_checks=list(_build_checks()))
