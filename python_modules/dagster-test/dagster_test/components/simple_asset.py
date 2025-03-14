from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_components import Component, ComponentLoadContext, ResolvableModel, ResolvedFrom


class SimpleAssetComponentModel(ResolvableModel):
    asset_key: str
    value: str


class SimpleAssetComponent(Component, ResolvedFrom[SimpleAssetComponentModel]):
    """A simple asset that returns a constant string value."""

    asset_key: str
    value: str

    def __init__(self, asset_key: AssetKey, value: str):
        self._asset_key = asset_key
        self._value = value

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self._asset_key)
        def dummy(context: AssetExecutionContext):
            return self._value

        return Definitions(assets=[dummy])
