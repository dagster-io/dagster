import dagster as dg
from dagster.components import (
    Component,
    Model,
    Resolvable,
    ComponentLoadContext,
    ResolvedAssetSpec,
)
from typing import Iterator
from dagster._core.pipes.transforms import (
    build_transform_defs,
    TransformSpec,
)
from dagster import AssetSpec

from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.subprocess import PipesSubprocessClient


class OpSpec(Model):
    name: str


class ScriptTransformSpec(Model, Resolvable):
    op: OpSpec
    assets: list[ResolvedAssetSpec]


class UvRunTransformComponent(Component, Model, Resolvable):
    script_path: str
    transforms: list[ScriptTransformSpec]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        component_path = context.path

        def invoke_fn(
            context: dg.AssetExecutionContext, op_name: str, spec: AssetSpec
        ) -> Iterator[PipesExecutionResult]:
            script_path = component_path / self.script_path
            assert script_path.exists(), f"Script {script_path} does not exist"
            invocation = PipesSubprocessClient().run(
                context=context,
                command=["uv", "run", script_path],
            )
            return invocation.get_results()

        return build_transform_defs(
            transform_specs=[
                TransformSpec(
                    op_name=transform.op.name,
                    assets=transform.assets,
                )
                for transform in self.transforms
            ],
            invoke_fn=invoke_fn,
        )
