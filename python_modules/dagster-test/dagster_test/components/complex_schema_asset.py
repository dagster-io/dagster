from collections.abc import Sequence
from typing import Annotated, Optional

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_components import Component, ComponentLoadContext
from dagster_components.core.schema.base import ResolvableSchema
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetPostProcessorSchema,
    OpSpecSchema,
    PostProcessorFn,
)
from pydantic import Field


class ComplexAssetSchema(ResolvableSchema["ComplexAssetComponent"]):
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


class ComplexAssetComponent(Component):
    """An asset that has a complex schema."""

    @classmethod
    def get_schema(cls):
        return ComplexAssetSchema

    def __init__(
        self,
        value: str,
        op_spec: Optional[OpSpecSchema],
        asset_attributes: Optional[AssetAttributesSchema],
        asset_post_processors: Sequence[PostProcessorFn],
    ):
        self._value = value
        self._op_spec = op_spec
        self._asset_attributes = asset_attributes
        self._asset_post_processors = asset_post_processors

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(spec=self._asset_attributes)
        def dummy(context: AssetExecutionContext):
            return self._value

        defs = Definitions(assets=[dummy])
        for post_processor in self._asset_post_processors:
            defs = post_processor(defs)
        return defs
