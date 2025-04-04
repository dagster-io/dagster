from dataclasses import dataclass
from datetime import datetime
from typing import Literal, NamedTuple, Optional, Union

import dagster as dg
import pandas as pd
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster.components import Component, ComponentLoadContext, Model, Resolvable
from typing_extensions import TypeAlias

HooliAssetCheckType: TypeAlias = Literal["static_threshold"]


class StaticThresholdCheck(Model):
    type: Literal["static_threshold"]
    asset: str
    check_name: str
    metric: str
    min: Optional[int]
    max: Optional[int]


# HooliAssetCheck: TypeAlias = Union[StaticThresholdCheck]
HooliAssetCheck: TypeAlias = StaticThresholdCheck


@dataclass
class HooliAssetChecksComponent(Component, Resolvable):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    checks: list[HooliAssetCheck]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        # Add definition construction logic here.
        def create_check_fn(hooli_asset_check: HooliAssetCheck) -> AssetChecksDefinition:
            if hooli_asset_check.type == "static_threshold":
                return build_static_threshold_asset_check(hooli_asset_check)
            else:
                raise NotImplementedError(f"Check type {check.type} is not implemented")

        check_defs = []
        for check in self.checks:
            check_defs.append(create_check_fn(check))
        return dg.Definitions(asset_checks=check_defs)


def build_static_threshold_asset_check(check: StaticThresholdCheck):
    @dg.asset_check(
        asset=dg.AssetKey.from_user_string(check.asset),
        name=check.check_name,
    )
    def _check() -> dg.AssetCheckResult:
        df = pd.DataFrame()  # todo get from upstream

        metric = build_metric(df, check.metric)
        assert isinstance(metric, ValueMetric)

        return evaluate_static_threshold(
            min_value=check.min,
            max_value=check.max,
            latest_value=metric.value,
        )

    return _check


class NumRowsMetric(NamedTuple):
    num_rows: int


class ValueMetric(NamedTuple):
    column: str
    metric_type: str
    value: int


def evaluate_static_threshold(
    latest_value: float, min_value: Optional[float] = None, max_value: Optional[float] = None
) -> dg.AssetCheckResult:
    passed = True

    latest_value_metadata = None

    if isinstance(latest_value, datetime):
        latest_value_metadata = dg.MetadataValue.timestamp(latest_value)
    else:
        latest_value_metadata = float(latest_value)  # For numeric consistency

    if isinstance(latest_value_metadata, pd.Timestamp):
        latest_value_metadata = latest_value_metadata.to_pydatetime()

    if isinstance(min_value, str):
        min_value_metadata = datetime.fromisoformat(min_value)
    else:
        min_value_metadata = min_value

    if isinstance(max_value, str):
        max_value_metadata = datetime.fromisoformat(max_value)
    else:
        max_value_metadata = max_value

    if min_value is not None and latest_value < min_value:
        passed = False
    if max_value is not None and latest_value > max_value:
        passed = False

    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "min_threshold": min_value_metadata,
            "max_threshold": max_value_metadata,
            "latest": latest_value_metadata,
        },
    )


Metric: TypeAlias = Union[NumRowsMetric, ValueMetric]


def column_name(metric_str: str) -> str:
    """Extracts the column name from a metric string."""
    return metric_str.split(":")[1]


def build_metric(asset_data, metric_str: str) -> "Metric":
    if metric_str == "num_rows":
        return NumRowsMetric(num_rows=len(asset_data))
    elif ":" in metric_str:
        metric_type, column_name = metric_str.split(":")[0], metric_str.split(":")[1]
        if metric_type == "sum":
            return ValueMetric(
                column=column_name,
                value=asset_data[column_name].sum(),
                metric_type=metric_type,
            )
        else:
            raise ValueError(f"Unknown metric: {metric_str}")
    else:
        raise ValueError(f"Unknown metric: {metric_str}")
