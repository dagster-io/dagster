from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Any

from dagster import AssetSpec, AutomationCondition, Definitions
from dagster_components import AssetAttributesSchema, Component, ComponentLoadContext
from dagster_components.core.schema.objects import resolve_asset_attributes_to_mapping
from dagster_components.core.schema.resolvable_from_schema import (
    DSLFieldResolver,
    DSLSchema,
    ResolvableFromSchema,
)


def my_custom_fn(a: str, b: str) -> str:
    return a + "|" + b


def my_custom_automation_condition(cron_schedule: str) -> AutomationCondition:
    return AutomationCondition.cron_tick_passed(cron_schedule) & ~AutomationCondition.in_progress()


class CustomScopeSchema(DSLSchema):
    asset_attributes: AssetAttributesSchema


@dataclass
class HasCustomScope(Component, ResolvableFromSchema[CustomScopeSchema]):
    asset_attributes: Annotated[
        Mapping[str, Any], DSLFieldResolver(resolve_asset_attributes_to_mapping)
    ]

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
