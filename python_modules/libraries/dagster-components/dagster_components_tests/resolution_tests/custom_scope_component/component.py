from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from dagster import AssetSpec, AutomationCondition, Definitions
from dagster_components import Component, ComponentLoadContext, Resolvable
from dagster_components.resolved.core_models import ResolvedAssetAttributes


def my_custom_fn(a: str, b: str) -> str:
    return a + "|" + b


def my_custom_automation_condition(cron_schedule: str) -> AutomationCondition:
    return AutomationCondition.cron_tick_passed(cron_schedule) & ~AutomationCondition.in_progress()


@dataclass
class HasCustomScope(Component, Resolvable):
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
        return Definitions(assets=[AssetSpec(key="key", **self.asset_attributes)])
