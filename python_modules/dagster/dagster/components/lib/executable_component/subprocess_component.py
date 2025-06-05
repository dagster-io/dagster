import os
import shlex
import shutil
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import Literal, Optional, Union

from dagster_shared import check

from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import (
    ExecutableComponent,
    OpMetadataSpec,
)


class ScriptSpec(OpMetadataSpec):
    type: Literal["script"] = "script"
    path: str
    args: Optional[Union[list[str], str]] = None

    @staticmethod
    def with_script_stem_as_default_name(
        script_runner_spec: "ScriptSpec",
    ) -> "ScriptSpec":
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


def get_cmd(script_runner_exe: str, spec: ScriptSpec, path: str) -> list[str]:
    abs_path = spec.path if os.path.isabs(spec.path) else os.path.join(path, spec.path)
    if isinstance(spec.args, str):
        return [script_runner_exe, abs_path, *shlex.split(spec.args)]
    elif isinstance(spec.args, list):
        return [script_runner_exe, abs_path, *spec.args]
    else:
        return [script_runner_exe, abs_path]


class SubprocessComponent(ExecutableComponent):
    execution: ScriptSpec

    @property
    def op_metadata_spec(self) -> OpMetadataSpec:
        return self._subprocess_spec

    @cached_property
    def _subprocess_spec(self) -> ScriptSpec:
        return ScriptSpec.with_script_stem_as_default_name(self.execution)

    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        component_load_context: ComponentLoadContext,
    ) -> Sequence[PipesExecutionResult]:
        assert not self.resource_keys, "Pipes subprocess scripts cannot have resources"
        return invoke_runner(
            context=context,
            command=get_cmd(
                script_runner_exe=check.not_none(shutil.which("python"), "python not found"),
                spec=self.execution,
                path=str(component_load_context.path),
            ),
        )
