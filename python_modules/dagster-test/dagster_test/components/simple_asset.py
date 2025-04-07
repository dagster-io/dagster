from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Component, ComponentLoadContext, ComponentSpec, Model, Resolvable


class SimpleAssetComponent(Component, Resolvable, Model):
    """A simple asset that returns a constant string value."""

    asset_key: str
    value: str

    def __init__(self, asset_key: AssetKey, value: str):
        self._asset_key = asset_key
        self._value = value

    @classmethod
    def get_spec(cls):
        return ComponentSpec(
            owners=["john@dagster.io", "jane@dagster.io"],
            tags=["a", "b", "c"],
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self._asset_key)
        def dummy(context: AssetExecutionContext):
            return self._value

        return Definitions(assets=[dummy])
