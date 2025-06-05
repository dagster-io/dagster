import os
import shutil
from collections.abc import Sequence
from functools import cached_property
from typing import Union

from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import (
    ExecutableComponent,
    OpMetadataSpec,
)
from dagster.components.lib.executable_component.subprocess_component import ScriptRunnerSpec


class UvRunComponent(ExecutableComponent):
    execution: ScriptRunnerSpec

    @property
    def op_metadata_spec(self) -> OpMetadataSpec:
        return self._script_runner_spec

    @cached_property
    def _script_runner_spec(self) -> ScriptRunnerSpec:
        return ScriptRunnerSpec.with_script_stem_as_default_name(self.execution)

    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        component_load_context: ComponentLoadContext,
    ) -> Sequence[PipesExecutionResult]:
        assert not self.resource_keys, "Pipes subprocess scripts cannot have resources"
        path = (
            self.execution.path
            if os.path.isabs(self.execution.path)
            else os.path.join(component_load_context.path, self.execution.path)
        )
        cmd = [shutil.which("uv"), "run", "--active", "--script", path] + (
            self.execution.args or []
        )
        invocation = PipesSubprocessClient().run(context=context.op_execution_context, command=cmd)
        return invocation.get_results()
