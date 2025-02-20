from collections.abc import Sequence
from typing import Annotated, Optional

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from pydantic import Field

from dagster_components import Component, ComponentLoadContext, registered_component_type
from dagster_components.core.component_scaffolder import DefaultComponentScaffolder
from dagster_components.core.schema.base import ResolvableSchema
from dagster_components.core.schema.metadata import ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetSpecTransformSchema,
    OpSpecSchema,
)


class ComplexAssetSchema(ResolvableSchema):
    value: str = Field(..., examples=["example_for_value"])
    list_value: list[str] = Field(
        ..., examples=[["example_for_list_value_1", "example_for_list_value_2"]]
    )
    obj_value: dict[str, str] = Field(..., examples=[{"key_1": "value_1", "key_2": "value_2"}])
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema], ResolvableFieldInfo(required_scope={"node"})
    ] = None
    asset_transforms: Optional[Sequence[AssetSpecTransformSchema]] = None


@registered_component_type(name="complex_schema_asset")
class ComplexSchemaAsset(Component):
    """An asset that has a complex schema."""

    @classmethod
    def get_schema(cls):
        return ComplexAssetSchema

    @classmethod
    def get_scaffolder(cls) -> DefaultComponentScaffolder:
        return DefaultComponentScaffolder()

    def __init__(
        self,
        value: str,
        op_spec: Optional[OpSpecSchema],
        asset_attributes: Optional[AssetAttributesSchema],
        asset_transforms: Sequence[AssetSpecTransformSchema],
    ):
        self._value = value
        self._op_spec = op_spec
        self._asset_attributes = asset_attributes
        self._asset_transforms = asset_transforms

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(spec=self._asset_attributes)
        def dummy(context: AssetExecutionContext):
            return self._value

        return Definitions(assets=[dummy])
