from dataclasses import dataclass

import dagster as dg
import pandas as pd
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster.components import Component, ComponentLoadContext, Resolvable

from components_yaml_checks_dsl.lib.hooli_asset_checks.check_types import (
    HooliAssetCheck,
    StaticThresholdCheck,
)
from components_yaml_checks_dsl.lib.hooli_asset_checks.engine import evaluate_static_threshold


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
    def _check(users: pd.DataFrame) -> dg.AssetCheckResult:
        return evaluate_static_threshold(users, check)

    return _check
