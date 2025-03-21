from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_components import Component, DefsLoadContext


class AllMetadataEmptyComponent(Component):
    def build_defs(self, context: DefsLoadContext) -> Definitions:
        @asset
        def hardcoded_asset(context: AssetExecutionContext):
            return 1

        return Definitions(assets=[hardcoded_asset])
