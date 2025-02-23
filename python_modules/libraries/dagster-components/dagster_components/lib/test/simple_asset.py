from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from pydantic import BaseModel

from dagster_components import Component, ComponentLoadContext, registered_component_type
from dagster_components.core.component_scaffolder import (
    ComponentScaffolder,
    DefaultComponentScaffolder,
)


class SimpleAssetSchema(BaseModel):
    asset_key: str
    value: str


@registered_component_type(name="simple_asset")
class SimpleAsset(Component):
    """A simple asset that returns a constant string value."""

    @classmethod
    def get_schema(cls):
        return SimpleAssetSchema

    @classmethod
    def get_scaffolder(cls) -> ComponentScaffolder:
        return DefaultComponentScaffolder()

    def __init__(self, asset_key: AssetKey, value: str):
        self._asset_key = asset_key
        self._value = value

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self._asset_key)
        def dummy(context: AssetExecutionContext):
            return self._value

        return Definitions(assets=[dummy])
