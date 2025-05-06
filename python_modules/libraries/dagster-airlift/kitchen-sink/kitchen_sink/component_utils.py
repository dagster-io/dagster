from dataclasses import dataclass

from dagster import Definitions
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Component, ComponentLoadContext, Resolvable


@dataclass(frozen=True)
class SimpleAssetComponent(Component, Resolvable):
    """A simple asset that returns a constant string value."""

    asset_key: str

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self.asset_key)
        def dummy(context: AssetExecutionContext):
            return "dummy"

        return Definitions(assets=[dummy])
