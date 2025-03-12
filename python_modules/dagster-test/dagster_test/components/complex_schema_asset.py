from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Optional

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_components import Component, ComponentLoadContext
from dagster_components.resolved.core_models import (
    AssetAttributesModel,
    AssetPostProcessor,
    AssetPostProcessorModel,
    OpSpecModel,
)
from dagster_components.resolved.metadata import ResolvableFieldInfo
from dagster_components.resolved.model import ResolvableModel, ResolvedFrom, Resolver
from pydantic import Field


class ComplexAssetModel(ResolvableModel):
    value: str = Field(..., examples=["example_for_value"])
    list_value: list[str] = Field(
        ..., examples=[["example_for_list_value_1", "example_for_list_value_2"]]
    )
    obj_value: dict[str, str] = Field(..., examples=[{"key_1": "value_1", "key_2": "value_2"}])
    op: Optional[OpSpecModel] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel], ResolvableFieldInfo(required_scope={"node"})
    ] = None
    asset_post_processors: Optional[Sequence[AssetPostProcessorModel]] = None


@dataclass
class ComplexAssetComponent(Component, ResolvedFrom[ComplexAssetModel]):
    """An asset that has a complex schema."""

    value: str
    list_value: list[str]
    obj_value: dict[str, str]
    op: Optional[OpSpecModel] = None
    asset_attributes: Optional[AssetAttributesModel] = None
    asset_post_processors: Annotated[
        Optional[Sequence[AssetPostProcessor]], Resolver.from_annotation()
    ] = None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(spec=self.asset_attributes)
        def dummy(context: AssetExecutionContext):
            return self.value

        defs = Definitions(assets=[dummy])
        for post_processor in self.asset_post_processors or []:
            defs = post_processor.fn(defs)
        return defs
