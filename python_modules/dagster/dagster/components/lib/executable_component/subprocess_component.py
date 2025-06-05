import os
import shlex
import shutil
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import Literal, Optional, Union

from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import (
    ExecutableComponent,
    OpMetadataSpec,
)


class ScriptRunnerSpec(OpMetadataSpec):
    type: Literal["subprocess"] = "subprocess"
    path: str
    args: Optional[Union[list[str], str]] = None

    @staticmethod
    def with_script_stem_as_default_name(
        script_runner_spec: "ScriptRunnerSpec",
    ) -> "ScriptRunnerSpec":
        name = (
            script_runner_spec.name
            if script_runner_spec.name
            else Path(script_runner_spec.path).stem
        )
        return script_runner_spec.model_copy(update={"name": name})


def invoke_runner(
    *,
    context: Union[AssetExecutionContext, AssetCheckExecutionContext],
    command: list[str],
) -> Sequence[PipesExecutionResult]:
    return (
        PipesSubprocessClient()
        .run(context=context.op_execution_context, command=command)
        .get_results()
    )


def get_cmd(script_runner_exec, execution: ScriptRunnerSpec, path: str) -> list[str]:
    abs_path = (
        execution.path if os.path.isabs(execution.path) else os.path.join(path, execution.path)
    )
    if isinstance(execution.args, str):
        return [script_runner_exec, abs_path, *shlex.split(execution.args)]
    elif isinstance(execution.args, list):
        return [script_runner_exec, abs_path, *execution.args]
    else:
        return [script_runner_exec, abs_path]


class SubprocessComponent(ExecutableComponent):
    execution: ScriptRunnerSpec

    @property
    def op_metadata_spec(self) -> OpMetadataSpec:
        return self._subprocess_spec

    @cached_property
    def _subprocess_spec(self) -> ScriptRunnerSpec:
        return ScriptRunnerSpec.with_script_stem_as_default_name(self.execution)

    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        component_load_context: ComponentLoadContext,
    ) -> Sequence[PipesExecutionResult]:
        assert not self.resource_keys, "Pipes subprocess scripts cannot have resources"
        which_python = shutil.which("python")
        assert which_python is not None
        return invoke_runner(
            context=context,
            command=get_cmd(
                script_runner_exec=which_python,
                execution=self.execution,
                path=str(component_load_context.path),
            ),
        )
