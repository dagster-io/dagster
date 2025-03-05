from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Optional

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_components import Component, ComponentLoadContext
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetPostProcessor,
    AssetPostProcessorSchema,
    OpSpecSchema,
)
from dagster_components.core.schema.resolvable_from_schema import ResolvableFromSchema, YamlSchema
from pydantic import Field


class ComplexAssetSchema(YamlSchema):
    value: str = Field(..., examples=["example_for_value"])
    list_value: list[str] = Field(
        ..., examples=[["example_for_list_value_1", "example_for_list_value_2"]]
    )
    obj_value: dict[str, str] = Field(..., examples=[{"key_1": "value_1", "key_2": "value_2"}])
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema], ResolvableFieldInfo(required_scope={"node"})
    ] = None
    asset_post_processors: Optional[Sequence[AssetPostProcessorSchema]] = None


@dataclass
class ComplexAssetComponent(Component, ResolvableFromSchema[ComplexAssetSchema]):
    """An asset that has a complex schema."""

    value: str
    list_value: list[str]
    obj_value: dict[str, str]
    op: Optional[OpSpecSchema] = None
    asset_attributes: Optional[AssetAttributesSchema] = None
    asset_post_processors: Annotated[
        Optional[Sequence[AssetPostProcessor]], AssetPostProcessor.from_optional_seq
    ] = None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(spec=self.asset_attributes)
        def dummy(context: AssetExecutionContext):
            return self.value

        defs = Definitions(assets=[dummy])
        for post_processor in self.asset_post_processors or []:
            defs = post_processor.fn(defs)
        return defs
