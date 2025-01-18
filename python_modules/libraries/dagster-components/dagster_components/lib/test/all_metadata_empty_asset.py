from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext, component_type
from dagster_components.core.component_scaffolder import DefaultComponentScaffolder


@component_type(name="all_metadata_empty_asset")
class AllMetadataEmptyAsset(Component):
    @classmethod
    def load(cls, context: "ComponentLoadContext") -> Self:
        return cls()

    @classmethod
    def get_scaffolder(cls) -> DefaultComponentScaffolder:
        return DefaultComponentScaffolder()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset
        def hardcoded_asset(context: AssetExecutionContext):
            return 1

        return Definitions(assets=[hardcoded_asset])
