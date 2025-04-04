from dataclasses import dataclass

import dagster as dg
import pandas as pd
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster.components import Component, ComponentLoadContext, Resolvable
from dagster_shared import check

from components_yaml_checks_dsl.lib.hooli_asset_checks.check_types import (
    HooliAssetCheck,
    StaticThresholdCheck,
)
from components_yaml_checks_dsl.lib.hooli_asset_checks.engine import evaluate_static_threshold


@dataclass
class HooliAssetChecksComponent(Component, Resolvable):
    """A fancy mini-framework for data quality."""

    checks: list[HooliAssetCheck]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        # Add definition construction logic here.

        check_defs: list[AssetChecksDefinition] = []
        for check_inst in self.checks:
            check_defs.append(create_asset_checks_def(check_inst))
        # import code

        # code.interact(local=locals())

        check.is_list(check_defs, of_type=AssetChecksDefinition)

        return dg.Definitions(asset_checks=check_defs)


def create_asset_checks_def(hooli_asset_check: HooliAssetCheck) -> AssetChecksDefinition:
    if hooli_asset_check.type == "static_threshold":
        return build_static_threshold_asset_check(hooli_asset_check)
    else:
        raise NotImplementedError(f"Check type {hooli_asset_check} is not implemented")


def build_static_threshold_asset_check(check: StaticThresholdCheck) -> dg.AssetChecksDefinition:
    @dg.asset_check(
        asset=dg.AssetKey.from_user_string(check.asset),
        name=check.check_name,
    )
    def _check(users: pd.DataFrame) -> dg.AssetCheckResult:
        return evaluate_static_threshold(users, check)

    return _check
