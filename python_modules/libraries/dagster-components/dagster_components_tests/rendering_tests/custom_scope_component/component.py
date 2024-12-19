from typing import Any, Mapping

from dagster import AssetSpec, AutomationCondition, Definitions
from dagster_components import Component, ComponentLoadContext, component
from pydantic import BaseModel


def my_custom_fn(a: str, b: str) -> str:
    return a + "|" + b


def my_custom_automation_condition(cron_schedule: str) -> AutomationCondition:
    return AutomationCondition.cron_tick_passed(cron_schedule) & ~AutomationCondition.in_progress()


class CustomScopeParams(BaseModel):
    attributes: Mapping[str, Any]


@component(name="custom_scope_component")
class HasCustomScope(Component):
    params_schema = CustomScopeParams

    @classmethod
    def get_rendering_scope(cls) -> Mapping[str, Any]:
        return {
            "custom_str": "xyz",
            "custom_dict": {"a": "b"},
            "custom_fn": my_custom_fn,
            "custom_automation_condition": my_custom_automation_condition,
        }

    def __init__(self, attributes: Mapping[str, Any]):
        self.attributes = attributes

    @classmethod
    def load(cls, context: ComponentLoadContext):
        loaded_params = context.load_params(cls.params_schema)
        return cls(attributes=loaded_params.attributes)

    def build_defs(self, context: ComponentLoadContext):
        return Definitions(assets=[AssetSpec(key="key", **self.attributes)])
