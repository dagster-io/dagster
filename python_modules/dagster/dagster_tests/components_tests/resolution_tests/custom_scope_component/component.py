from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import dagster as dg
from dagster import AutomationCondition, ComponentLoadContext
from dagster.components.resolved.core_models import ResolvedAssetAttributes


def my_custom_fn(a: str, b: str) -> str:
    return a + "|" + b


def my_custom_automation_condition(cron_schedule: str) -> dg.AutomationCondition:
    return AutomationCondition.cron_tick_passed(cron_schedule) & ~AutomationCondition.in_progress()


@dataclass
class HasCustomScope(dg.Component, dg.Resolvable):
    asset_attributes: ResolvedAssetAttributes

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {
            "custom_str": "xyz",
            "custom_dict": {"a": "b"},
            "custom_fn": my_custom_fn,
            "custom_automation_condition": my_custom_automation_condition,
        }

    def build_defs(self, context: ComponentLoadContext):
        return dg.Definitions(assets=[dg.AssetSpec(key="key", **self.asset_attributes)])
