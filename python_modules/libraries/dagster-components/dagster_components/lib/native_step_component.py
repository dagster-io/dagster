from abc import abstractmethod
from typing import Any, Optional, Sequence

from dagster import multi_asset
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster_embedded_elt.sling.resources import AssetExecutionContext
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import ComponentGenerateRequest
from dagster_components.core.dsl_schema import OpSpecBaseModel


class AssetSpecBaseModel(BaseModel):
    key: str


class NativeStepComponentSchema(BaseModel):
    op: OpSpecBaseModel
    assets: Optional[Sequence[AssetSpecBaseModel]] = None


# Possibilities
# * op
# * step
# * task
# * computation


class NativeStepComponent(Component):
    params_schema = NativeStepComponentSchema

    def __init__(self, op: OpSpecBaseModel, assets: Optional[Sequence[AssetSpecBaseModel]]):
        self.op = op
        self.assets = assets or []

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @multi_asset(
            name=self.op.name,
            specs=[AssetSpec(AssetKey.from_user_string(asset.key)) for asset in self.assets],
        )
        def _the_step(context: AssetExecutionContext):
            return self.execute(context)

        return Definitions([_the_step])

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        # all paths should be resolved relative to the directory we're in
        loaded_params = context.load_params(cls.params_schema)

        return cls(op=loaded_params.op, assets=loaded_params.assets)

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: Any) -> None:
        super().generate_files(request, params)

    @abstractmethod
    def execute(self, context: AssetExecutionContext): ...
