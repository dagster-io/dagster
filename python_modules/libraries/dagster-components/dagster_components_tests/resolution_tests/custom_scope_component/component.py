from collections.abc import Mapping
from typing import Any

from dagster import AssetSpec, AutomationCondition, Definitions
from dagster_components import (
    AssetAttributesSchema,
    Component,
    ComponentLoadContext,
    ResolvableSchema,
    registered_component_type,
)


def my_custom_fn(a: str, b: str) -> str:
    return a + "|" + b


def my_custom_automation_condition(cron_schedule: str) -> AutomationCondition:
    return AutomationCondition.cron_tick_passed(cron_schedule) & ~AutomationCondition.in_progress()


class CustomScopeSchema(ResolvableSchema):
    asset_attributes: AssetAttributesSchema


@registered_component_type(name="custom_scope_component")
class HasCustomScope(Component):
    asset_attributes: Mapping[str, Any]

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {
            "custom_str": "xyz",
            "custom_dict": {"a": "b"},
            "custom_fn": my_custom_fn,
            "custom_automation_condition": my_custom_automation_condition,
        }

    @classmethod
    def get_schema(cls):
        return CustomScopeSchema

    def build_defs(self, context: ComponentLoadContext):
        return Definitions(assets=[AssetSpec(key="key", **self.asset_attributes)])
