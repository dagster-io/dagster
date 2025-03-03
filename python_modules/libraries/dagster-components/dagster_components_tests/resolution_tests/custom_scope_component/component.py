from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Any

from dagster import AssetSpec, AutomationCondition, Definitions
from dagster_components import AssetAttributesSchema, Component, ComponentLoadContext, FieldResolver
from dagster_components.core.schema.base import PlainSamwiseSchema
from dagster_components.core.schema.objects import resolve_asset_attributes_to_mapping


def my_custom_fn(a: str, b: str) -> str:
    return a + "|" + b


def my_custom_automation_condition(cron_schedule: str) -> AutomationCondition:
    return AutomationCondition.cron_tick_passed(cron_schedule) & ~AutomationCondition.in_progress()


class CustomScopeSchema(PlainSamwiseSchema):
    asset_attributes: AssetAttributesSchema


@dataclass
class HasCustomScope(Component):
    asset_attributes: Annotated[
        Mapping[str, Any],
        FieldResolver(
            lambda context, schema: resolve_asset_attributes_to_mapping(
                context=context, schema=schema.asset_attributes
            )
        ),
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
