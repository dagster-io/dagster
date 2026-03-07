from dataclasses import dataclass

from dagster import Component, ComponentLoadContext, Resolvable
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.resolved.core_models import OpSpec, ResolvedAssetAttributes


@dataclass
class ComplexAssetComponent(Component, Resolvable):
    """An asset that has a complex schema."""

    value: str
    list_value: list[str]
    obj_value: dict[str, str]
    op: OpSpec | None = None
    asset_attributes: ResolvedAssetAttributes | None = None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(spec=self.asset_attributes)
        def dummy(context: AssetExecutionContext):
            return self.value

        return Definitions(assets=[dummy])
