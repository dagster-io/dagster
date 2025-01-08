from collections.abc import Sequence
from typing import Annotated, Optional

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from pydantic import BaseModel

from dagster_components import (
    AssetSpecTransformModel,
    Component,
    ComponentLoadContext,
    ResolvableFieldInfo,
    component_type,
)
from dagster_components.core.component_generator import (
    ComponentGenerator,
    DefaultComponentGenerator,
)
from dagster_components.core.schema.objects import AssetAttributesModel, OpSpecBaseModel


class ComplexAssetParams(BaseModel):
    value: str
    op: Optional[OpSpecBaseModel] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel], ResolvableFieldInfo(additional_scope={"node"})
    ] = None
    asset_transforms: Optional[Sequence[AssetSpecTransformModel]] = None


@component_type(name="complex_schema_asset")
class ComplexSchemaAsset(Component):
    """An asset that has a complex params schema."""

    @classmethod
    def get_component_schema_type(cls):
        return ComplexAssetParams

    @classmethod
    def get_generator(cls) -> ComponentGenerator:
        return DefaultComponentGenerator()

    def __init__(
        self,
        value: str,
        op_spec: Optional[OpSpecBaseModel],
        asset_attributes: Optional[AssetAttributesModel],
        asset_transforms: Sequence[AssetSpecTransformModel],
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
