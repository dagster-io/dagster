import os
import shlex
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional, Union

from dagster.components.lib.executable_component.component import OpSpec

if TYPE_CHECKING:
    from dagster._core.execution.context.asset_check_execution_context import (
        AssetCheckExecutionContext,
    )
    from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
    from dagster._core.pipes.context import PipesExecutionResult


class ScriptSpec(OpSpec):
    type: Literal["script"] = "script"
    path: str
    args: Optional[Union[list[str], str]] = None

    @staticmethod
    def with_script_stem_as_default_name(
        script_runner_spec: "ScriptSpec",
    ) -> "ScriptSpec":
        return script_runner_spec.model_copy(
            update={
                "name": script_runner_spec.name
                if script_runner_spec.name
                else Path(script_runner_spec.path).stem
            }
        )


def invoke_runner(
    *, context: Union["AssetExecutionContext", "AssetCheckExecutionContext"], command: list[str]
) -> Sequence["PipesExecutionResult"]:
    from dagster._core.pipes.subprocess import PipesSubprocessClient

    return (
        PipesSubprocessClient()
        .run(context=context.op_execution_context, command=command)
        .get_results()
    )


def get_cmd(script_runner_exe: list[str], spec: ScriptSpec, path: str) -> list[str]:
    abs_path = spec.path if os.path.isabs(spec.path) else os.path.join(path, spec.path)
    if isinstance(spec.args, str):
        return [*script_runner_exe, abs_path, *shlex.split(spec.args)]
    elif isinstance(spec.args, list):
        return [*script_runner_exe, abs_path, *spec.args]
    else:
        return [*script_runner_exe, abs_path]
