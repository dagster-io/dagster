from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Optional

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster_components import (
    AssetSpecTransformModel,
    Component,
    ComponentLoadContext,
    ResolvableFieldInfo,
    component_type,
)
from dagster_components.core.component_decl_builder import YamlComponentDecl
from dagster_components.core.component_generator import (
    ComponentGenerator,
    DefaultComponentGenerator,
)
from dagster_components.core.schema.objects import AssetAttributesModel, OpSpecBaseModel

if TYPE_CHECKING:
    from dagster_components.core.component import ComponentDeclNode


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
    def get_params_schema_type(cls):
        return ComplexAssetParams

    @classmethod
    def get_generator(cls) -> ComponentGenerator:
        return DefaultComponentGenerator()

    @classmethod
    def from_decl_node(
        cls, context: "ComponentLoadContext", decl_node: "ComponentDeclNode"
    ) -> Self:
        assert isinstance(decl_node, YamlComponentDecl)
        loaded_params = TypeAdapter(cls.get_params_schema_type()).validate_python(
            decl_node.component_file_model.params
        )
        return cls(
            value=loaded_params.value,
            op_spec=loaded_params.op,
            asset_attributes=loaded_params.asset_attributes,
            asset_transforms=loaded_params.asset_transforms or [],
        )

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
