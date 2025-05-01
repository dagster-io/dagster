from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Component, ComponentLoadContext
from dagster.components.scaffold.scaffold import Scaffolder, scaffold_with


class AllMetadataEmptyComponentScaffolder(Scaffolder):
    @classmethod
    def supports_multi_document_yaml(cls) -> bool:
        return True


@scaffold_with(AllMetadataEmptyComponentScaffolder)
class AllMetadataEmptyComponent(Component):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset
        def hardcoded_asset(context: AssetExecutionContext):
            return 1

        return Definitions(assets=[hardcoded_asset])
