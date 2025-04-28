from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Component, ComponentLoadContext, ComponentTypeSpec, Model, Resolvable
from dagster.components.resolved.core_models import ResolvedAssetKey


class SimpleAssetComponent(Component, Resolvable, Model):
    """A simple asset that returns a constant string value."""

    asset_key: ResolvedAssetKey
    value: str

    @classmethod
    def get_spec(cls):
        return ComponentTypeSpec(
            owners=["john@dagster.io", "jane@dagster.io"],
            tags=["a", "b", "c"],
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self.asset_key)
        def dummy(context: AssetExecutionContext):
            return self.value

        return Definitions(assets=[dummy])
