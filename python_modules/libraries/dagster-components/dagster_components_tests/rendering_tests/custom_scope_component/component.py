from collections.abc import Mapping
from typing import Any

from dagster import AssetSpec, AutomationCondition, Definitions
from dagster_components import Component, ComponentLoadContext, component_type
from pydantic import BaseModel


def my_custom_fn(a: str, b: str) -> str:
    return a + "|" + b


def my_custom_automation_condition(cron_schedule: str) -> AutomationCondition:
    return AutomationCondition.cron_tick_passed(cron_schedule) & ~AutomationCondition.in_progress()


class CustomScopeParams(BaseModel):
    attributes: Mapping[str, Any]


@component_type(name="custom_scope_component")
class HasCustomScope(Component):
    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {
            "custom_str": "xyz",
            "custom_dict": {"a": "b"},
            "custom_fn": my_custom_fn,
            "custom_automation_condition": my_custom_automation_condition,
        }

    def __init__(self, attributes: Mapping[str, Any]):
        self.attributes = attributes

    @classmethod
    def get_schema(cls):
        return CustomScopeParams

    @classmethod
    def load(cls, context: ComponentLoadContext):
        loaded_params = context.load_params(cls.get_schema())
        return cls(attributes=loaded_params.attributes)

    def build_defs(self, context: ComponentLoadContext):
        return Definitions(assets=[AssetSpec(key="key", **self.attributes)])
