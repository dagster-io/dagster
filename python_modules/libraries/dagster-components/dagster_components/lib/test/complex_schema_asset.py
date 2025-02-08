from collections.abc import Sequence
from typing import Annotated, Optional

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext

from dagster_components import Component, ComponentLoadContext, registered_component_type
from dagster_components.core.component_scaffolder import DefaultComponentScaffolder
from dagster_components.core.schema.base import ComponentSchema
from dagster_components.core.schema.metadata import SchemaFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    AssetSpecTransformSchema,
    OpSpecSchema,
)


class ComplexAssetParams(ComponentSchema):
    value: str
    op: Optional[OpSpecSchema] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesSchema], SchemaFieldInfo(required_scope={"node"})
    ] = None
    asset_transforms: Optional[Sequence[AssetSpecTransformSchema]] = None


@registered_component_type(name="complex_schema_asset")
class ComplexSchemaAsset(Component):
    """An asset that has a complex params schema."""

    @classmethod
    def get_schema(cls):
        return ComplexAssetParams

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
