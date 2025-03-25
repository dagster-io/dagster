from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_components import Component, DefsModuleLoadContext


class AllMetadataEmptyComponent(Component):
    def build_defs(self, context: DefsModuleLoadContext) -> Definitions:
        @asset
        def hardcoded_asset(context: AssetExecutionContext):
            return 1

        return Definitions(assets=[hardcoded_asset])
