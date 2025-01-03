from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional, Sequence

from dagster import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from pydantic import BaseModel
from typing_extensions import Self

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.component import ComponentGenerateRequest
from dagster_components.core.dsl_schema import AssetSpecModel, OpSpecBaseModel


class NativeStepComponentSchema(BaseModel):
    op: OpSpecBaseModel
    assets: Optional[Sequence[AssetSpecModel]] = None


# Possibilities
# * op
# * step
# * task
# * computation


class NativeStepComponent(Component):
    params_schema = NativeStepComponentSchema

    def __init__(
        self, op: OpSpecBaseModel, assets: Optional[Sequence[AssetSpecModel]], script_path: Path
    ):
        self.op = op
        self.assets = assets or []
        self.script_path = script_path

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @multi_asset(
            name=self.op.name,
            op_tags=self.op.tags,
            specs=[asset.render_spec(context.templated_value_resolver) for asset in self.assets],
        )
        def _the_step(context: AssetExecutionContext):
            return self.execute(context)

        return Definitions([_the_step])

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        # all paths should be resolved relative to the directory we're in
        loaded_params = context.load_params(cls.params_schema)

        return cls(
            op=loaded_params.op, assets=loaded_params.assets, script_path=context.path / "step.py"
        )

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: Any) -> None:
        super().generate_files(request, params)

    @abstractmethod
    def execute(self, context: AssetExecutionContext): ...
