from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_components import Component, ComponentLoadContext
from dagster_components.resolved.core_models import ResolvedAssetKey
from dagster_components.resolved.model import Resolved


class SimpleAssetComponent(Component, Resolved):
    """A simple asset that returns a constant string value."""

    def __init__(
        self,
        asset_key: ResolvedAssetKey,
        value: str,
    ):
        self._asset_key = asset_key
        self._value = value

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self._asset_key)
        def dummy(context: AssetExecutionContext):
            return self._value

        return Definitions(assets=[dummy])
