from typing import Optional

from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster._components import (
    Component,
    ComponentInitContext,
    ComponentLoadContext,
    global_component,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext


class SimpleAssetParams(BaseModel):
    asset_key: str
    value: str


@global_component
class SimpleAsset(Component):
    params_schema = Optional[SimpleAssetParams]

    @classmethod
    def from_component_params(
        cls, init_context: ComponentInitContext, component_params: object
    ) -> Self:
        loaded_params = TypeAdapter(cls.params_schema).validate_python(component_params)
        return cls(
            asset_key=AssetKey.from_user_string(loaded_params.asset_key),  # type: ignore
            value=loaded_params.value,  # type: ignore
        )

    def __init__(self, asset_key: AssetKey, value: str):
        self._asset_key = asset_key
        self._value = value

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self._asset_key)
        def dummy(context: AssetExecutionContext):
            return self._value

        return Definitions(assets=[dummy])
