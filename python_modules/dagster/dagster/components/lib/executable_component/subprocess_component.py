import os
import shutil
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import Literal, Union

from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import (
    ExecutableComponent,
    OpMetadataSpec,
)


class SubprocessSpec(OpMetadataSpec):
    type: Literal["subprocess"] = "subprocess"
    path: str


class SubprocessComponent(ExecutableComponent):
    execution: SubprocessSpec

    @property
    def op_metadata_spec(self) -> OpMetadataSpec:
        return self._subprocess_spec

    @cached_property
    def _subprocess_spec(self) -> SubprocessSpec:
        name = self.execution.name if self.execution.name else Path(self.execution.path).stem
        return self.execution.model_copy(update={"name": name})

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
        cmd = [shutil.which("python"), path]
        invocation = PipesSubprocessClient().run(context=context.op_execution_context, command=cmd)
        return invocation.get_results()
